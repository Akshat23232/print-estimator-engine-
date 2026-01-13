"""
Intake Request/Response Schemas

Pydantic models for the /intake endpoint.

Design Decisions:
1. Use Literal types for input_type to enforce valid options
2. Optional fields allow partial submissions
3. Response always includes validation result, even on success
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.schemas.print_specs import PrintSpecs, ValidationResult, PriceEstimate


class IntakeRequest(BaseModel):
    """
    Request body for the /intake endpoint.
    
    Supports three input types:
    - text: Plain text description of print job
    - pdf: PDF document metadata (actual parsing is TODO)
    - image: Image metadata (actual OCR is TODO)
    
    Examples:
        Text input:
        {"input_type": "text", "content": "500 business cards, double-sided"}
        
        PDF metadata:
        {"input_type": "pdf", "metadata": {"filename": "specs.pdf", "pages": 2}}
    """
    
    input_type: Literal["text", "pdf", "image"] = Field(
        description="Type of input being submitted"
    )
    
    content: Optional[str] = Field(
        default=None,
        description="Text content for direct text input, or extracted text from documents"
    )
    
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata for PDF/image inputs (filename, size, etc.)"
    )
    
    # TODO: Add file upload support
    # file: Optional[UploadFile] = None
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "input_type": "text",
                    "content": "I need 500 business cards, double-sided printing, matte finish with rounded corners"
                },
                {
                    "input_type": "pdf",
                    "content": "Extracted text from PDF...",
                    "metadata": {
                        "filename": "print_specs.pdf",
                        "pages": 2,
                        "file_size_bytes": 102400
                    }
                }
            ]
        }


class IntakeResponse(BaseModel):
    """
    Response from the /intake endpoint.
    
    Always includes:
    - request_id: Unique identifier for tracking
    - status: Overall processing status
    - validation: Validation result with errors/warnings
    
    Optionally includes (if extraction successful):
    - extracted_specs: Parsed print specifications
    - estimate: Price estimate
    
    Design Decision: Always return validation info, even on success.
    This helps clients understand confidence level and potential issues.
    """
    
    request_id: str = Field(
        description="Unique identifier for this request"
    )
    
    status: Literal["success", "validation_errors", "extraction_failed"] = Field(
        description="Overall processing status"
    )
    
    extracted_specs: Optional[PrintSpecs] = Field(
        default=None,
        description="Extracted print specifications (null if extraction failed)"
    )
    
    validation: ValidationResult = Field(
        description="Validation result with any errors or warnings"
    )
    
    estimate: Optional[PriceEstimate] = Field(
        default=None,
        description="Price estimate (null if specs invalid or pricing failed)"
    )
