"""
Intake Endpoint Router

Handles incoming print job requests and orchestrates the extraction,
validation, and pricing pipeline.

╔═══════════════════════════════════════════════════════════════════════════╗
║  PIPELINE OVERVIEW                                                         ║
║                                                                             ║
║  1. EXTRACT   → LLM parses natural language → PrintSpecs (AI)             ║
║  2. VALIDATE  → Business rules check → Errors/Warnings (Rules)            ║
║  3. PRICE     → Deterministic calculation → PriceEstimate (Rules)         ║
║  4. NOTIFY    → Fire-and-forget webhook → n8n workflow                    ║
║  5. RESPOND   → Return complete result → Client                           ║
║                                                                             ║
║  Design Decisions:                                                         ║
║  1. Single endpoint handles text, PDF metadata, and image metadata         ║
║  2. Response includes ALL extracted data, even if partially invalid        ║
║  3. Validation errors don't prevent response - they're flagged clearly     ║
║  4. Async webhook to n8n doesn't block response                           ║
║  5. AI is used ONLY in step 1 (extraction)                                ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import logging
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.config import get_settings
from app.schemas.intake import IntakeRequest, IntakeResponse
from app.schemas.print_specs import PrintSpecs, ValidationResult, PriceEstimate
from app.services.llm_extractor import extract_print_specs
from app.services.pricing import calculate_price
from app.services.validator import validate_specs

logger = logging.getLogger(__name__)
router = APIRouter()


async def send_to_n8n(webhook_url: str, payload: dict) -> None:
    """
    Fire-and-forget webhook to n8n.
    
    Design Decision: Async background task that doesn't block main response.
    We log failures but don't retry (n8n can handle that if needed).
    
    TODO: Add retry logic with exponential backoff
    TODO: Add dead letter queue for failed webhooks
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"n8n webhook success: {response.status_code}")
    except Exception as e:
        # Log but don't raise - this is a background task
        logger.error(f"n8n webhook failed: {e}")


@router.post("/intake", response_model=IntakeResponse)
async def intake_print_job(
    request: IntakeRequest,
    background_tasks: BackgroundTasks
) -> IntakeResponse:
    """
    Accept print job specification and return structured estimate.
    
    Pipeline:
    1. Extract specs from input using LLM
    2. Validate extracted specs
    3. Calculate pricing
    4. Queue n8n webhook (if configured)
    5. Return complete response
    
    Args:
        request: Input containing text, PDF metadata, or image metadata
        background_tasks: FastAPI background task queue for async operations
        
    Returns:
        IntakeResponse with extracted specs, validation result, and price estimate
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Processing intake request {request_id}, type: {request.input_type}")
    
    settings = get_settings()
    
    # Step 1: Extract print specifications using LLM
    # This is where the magic happens - LLM parses natural language into structured data
    try:
        extracted_specs = await extract_print_specs(
            input_type=request.input_type,
            content=request.content,
            metadata=request.metadata
        )
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        # Return partial response with extraction error
        # Design Decision: Don't fail completely - show what we could determine
        return IntakeResponse(
            request_id=request_id,
            status="extraction_failed",
            extracted_specs=None,
            validation=ValidationResult(
                is_valid=False,
                errors=[f"Failed to extract specifications: {str(e)}"],
                warnings=[]
            ),
            estimate=None
        )
    
    # Step 2: Validate extracted specifications
    # Checks for required fields, valid ranges, and business rules
    validation_result = validate_specs(extracted_specs)
    
    # Step 3: Calculate pricing (only if specs are valid enough)
    # Pricing requires at minimum: product_type and quantity
    estimate: Optional[PriceEstimate] = None
    if extracted_specs and extracted_specs.product_type and extracted_specs.quantity:
        try:
            estimate = calculate_price(extracted_specs)
        except Exception as e:
            logger.error(f"Pricing calculation failed: {e}")
            # Add pricing error to warnings (not errors - validation already passed)
            if hasattr(validation_result, 'warnings'):
                validation_result.warnings.append(f"Could not calculate price: {str(e)}")
    
    # Step 4: Queue n8n webhook (async, non-blocking)
    if settings.n8n_webhook_url:
        webhook_payload = {
            "request_id": request_id,
            "specs": extracted_specs.model_dump() if extracted_specs else None,
            "validation": validation_result.model_dump(),
            "estimate": estimate.model_dump() if estimate else None,
            "source": request.input_type,
        }
        background_tasks.add_task(send_to_n8n, settings.n8n_webhook_url, webhook_payload)
    
    # Step 5: Return complete response
    return IntakeResponse(
        request_id=request_id,
        status="success" if validation_result.is_valid else "validation_errors",
        extracted_specs=extracted_specs,
        validation=validation_result,
        estimate=estimate
    )
