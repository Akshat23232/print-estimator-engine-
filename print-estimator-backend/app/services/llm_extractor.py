"""
LLM-based Print Specification Extractor

Uses OpenAI-compatible API to extract structured print specifications
from natural language input.

╔═══════════════════════════════════════════════════════════════════════════╗
║  THIS IS THE ONLY MODULE THAT USES AI/LLM                                  ║
║                                                                             ║
║  Why AI here?                                                              ║
║  • Natural language is ambiguous: "500 cards" vs "five hundred BC"         ║
║  • Synonyms: "glossy" = "gloss" = "shiny coating"                          ║
║  • Abbreviations: "BC" = "business cards", "2-sided" = "double"            ║
║  • Typos: "bussiness cards" should still work                              ║
║                                                                             ║
║  Why NOT AI for pricing/validation?                                        ║
║  • Pricing must be deterministic and auditable                             ║
║  • Same input must always produce same price                               ║
║  • Legal/financial requirements demand calculation transparency            ║
╚═══════════════════════════════════════════════════════════════════════════╝

Design Decisions:
1. Structured JSON output via system prompt with example
2. Temperature = 0 for consistent extraction (minimize randomness)
3. Graceful handling of partial extractions (better than nothing)
4. OpenAI-compatible API (works with local models like Ollama)
"""

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas.print_specs import PrintSpecs

logger = logging.getLogger(__name__)


# ============================================================================
# EXTRACTION PROMPT
# ============================================================================

# Design Decision: Explicit format with example produces more reliable output
# than schema-only descriptions. The example acts as few-shot learning.
EXTRACTION_PROMPT = """You are a print specification extraction assistant. 
Your job is to extract structured print job specifications from user input.

Extract the following fields when present:
- product_type: Type of print product (business_cards, flyers, posters, brochures, booklets, stickers, banners, postcards, letterhead, envelopes)
- quantity: Number of units (integer)
- size: Dimensions or standard size name
- paper_stock: Paper type and weight
- sides: "single" or "double"
- finish: Surface finish (matte, gloss, satin, uncoated, soft_touch)
- color_mode: "full_color", "black_white", or "spot_color"
- options: Array of additional options (rounded_corners, foil_stamping, embossing, spot_uv, die_cut, hole_punch, scoring, perforation)
- turnaround_days: Number of days if mentioned (same-day = 0, next-day = 1, etc.)
- is_rush: true if urgency is indicated

IMPORTANT:
- Only extract information that is explicitly stated or clearly implied
- Use null for any field that cannot be determined
- Normalize product types to snake_case
- Normalize quantity to integers (e.g., "five hundred" → 500)
- Return ONLY valid JSON, no markdown or explanation

Example input: "I need 500 business cards, double-sided, matte finish"
Example output:
{
  "product_type": "business_cards",
  "quantity": 500,
  "size": null,
  "paper_stock": null,
  "sides": "double",
  "finish": "matte",
  "color_mode": null,
  "options": [],
  "turnaround_days": null,
  "is_rush": false
}
"""


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

async def extract_print_specs(
    input_type: str,
    content: Optional[str],
    metadata: Optional[dict]
) -> Optional[PrintSpecs]:
    """
    Extract print specifications from input using LLM.
    
    This is where AI adds value: handling natural language ambiguity.
    
    Args:
        input_type: Type of input ("text", "pdf", "image")
        content: Text content to parse
        metadata: Additional metadata for context (e.g., PDF page count)
        
    Returns:
        PrintSpecs object with extracted fields, or None if extraction fails
        
    Design Decisions:
        1. Always attempt extraction even with minimal input
           (partial results are better than no results)
        2. Use temperature=0 for deterministic extraction
           (same input should produce same extraction)
        3. Gracefully handle JSON parsing failures
           (LLMs sometimes add markdown or explanations)
    """
    settings = get_settings()
    
    # ── Build User Message Based on Input Type ─────────────────────────────
    # Each input type may need different preprocessing
    if input_type == "text":
        if not content:
            logger.warning("Text input type but no content provided")
            return None
        user_message = content
        
    elif input_type == "pdf":
        # ────────────────────────────────────────────────────────────────────
        # TODO: PRODUCTION ENHANCEMENT - PDF Parsing
        # 
        # In production, integrate actual PDF parsing:
        # - pypdf/pdfplumber for text extraction
        # - AWS Textract for complex layouts/tables
        # - Google Document AI for scanned documents
        #
        # Current behavior: Use provided content or metadata description
        # This allows frontend to send pre-extracted text from PDF
        # ────────────────────────────────────────────────────────────────────
        user_message = content or f"PDF document: {json.dumps(metadata or {})}"
        logger.info("PDF input received - using metadata/text content for extraction")
        
    elif input_type == "image":
        # ────────────────────────────────────────────────────────────────────
        # TODO: PRODUCTION ENHANCEMENT - Image/OCR Parsing
        #
        # In production, integrate OCR:
        # - Tesseract for simple text extraction
        # - AWS Textract for printed forms/documents
        # - Google Vision API for complex images
        # - GPT-4 Vision for image understanding
        #
        # Current behavior: Use provided content or metadata description
        # This allows frontend to send OCR results or image descriptions
        # ────────────────────────────────────────────────────────────────────
        user_message = content or f"Image document: {json.dumps(metadata or {})}"
        logger.info("Image input received - using metadata/text content for extraction")
        
    else:
        logger.error(f"Unknown input type: {input_type}")
        return None
    
    # ── Initialize OpenAI Client ───────────────────────────────────────────
    # Design Decision: AsyncOpenAI for non-blocking I/O in FastAPI
    # The base_url parameter allows using local models (Ollama, vLLM, etc.)
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url
    )
    
    try:
        logger.debug(f"Sending to LLM: {user_message[:200]}...")
        
        # ── Make API Call ──────────────────────────────────────────────────
        # Design Decision: temperature=0 for deterministic extraction
        # This minimizes randomness, making same input produce same output
        # (as close as possible for LLMs)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0,      # Deterministic for extraction tasks
            max_tokens=500,     # Extraction shouldn't need more
        )
        
        # ── Parse Response ─────────────────────────────────────────────────
        response_text = response.choices[0].message.content
        logger.debug(f"LLM response: {response_text}")
        
        # Clean up response (some models wrap JSON in markdown code blocks)
        # Example: ```json\n{...}\n```
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])  # Remove first and last lines
        
        # Parse JSON
        extracted_data = json.loads(cleaned)
        
        # Add raw input for debugging and audit trail
        extracted_data["raw_input"] = user_message
        
        # Create PrintSpecs object (Pydantic validates the data)
        specs = PrintSpecs(**extracted_data)
        logger.info(f"Extracted specs: product={specs.product_type}, qty={specs.quantity}")
        
        return specs
        
    except json.JSONDecodeError as e:
        # ────────────────────────────────────────────────────────────────────
        # JSON parsing failed - LLM didn't return valid JSON
        # This can happen when:
        # - Model adds explanations: "Here's the JSON: {...}"
        # - Model uses markdown: "```json\n{...}\n```"
        # - Model outputs invalid JSON: trailing commas, missing quotes
        #
        # TODO: Implement retry with stricter prompt or use structured output
        # ────────────────────────────────────────────────────────────────────
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return None
        
    except Exception as e:
        # Let router handle other errors (API failures, timeouts, etc.)
        logger.error(f"LLM extraction error: {e}")
        raise
