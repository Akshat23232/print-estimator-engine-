"""
Print Specification Schemas

Core domain models for print job specifications.

Design Decisions:
1. All fields optional - LLM may extract partial data
2. Validation happens AFTER extraction (separate concern)
3. Include raw input for audit trail
4. Detailed price breakdown for transparency
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class PrintSpecs(BaseModel):
    """
    Extracted print job specifications.
    
    This is the core domain model that the LLM extracts from input.
    All fields are optional because extraction may be partial.
    
    Fields map to common print industry terminology:
    - product_type: What's being printed (cards, flyers, posters, etc.)
    - quantity: Number of units
    - size: Dimensions (standard sizes or custom)
    - paper_stock: Paper type and weight
    - sides: Single or double-sided
    - finish: Matte, gloss, uncoated, etc.
    - options: Additional features (rounded corners, foil, etc.)
    """
    
    product_type: Optional[str] = Field(
        default=None,
        description="Type of print product (business_cards, flyers, posters, brochures, etc.)"
    )
    
    quantity: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of units to print"
    )
    
    size: Optional[str] = Field(
        default=None,
        description="Size specification (e.g., '3.5x2', 'A4', '11x17')"
    )
    
    paper_stock: Optional[str] = Field(
        default=None,
        description="Paper type and weight (e.g., '14pt', '100lb gloss', 'recycled')"
    )
    
    sides: Optional[Literal["single", "double"]] = Field(
        default=None,
        description="Single or double-sided printing"
    )
    
    finish: Optional[str] = Field(
        default=None,
        description="Finish type (matte, gloss, satin, uncoated)"
    )
    
    color_mode: Optional[Literal["full_color", "black_white", "spot_color"]] = Field(
        default=None,
        description="Color printing mode"
    )
    
    options: list[str] = Field(
        default_factory=list,
        description="Additional options (rounded_corners, foil_stamping, embossing, etc.)"
    )
    
    # Turnaround and rush handling
    turnaround_days: Optional[int] = Field(
        default=None,
        description="Requested turnaround time in business days"
    )
    
    is_rush: Optional[bool] = Field(
        default=False,
        description="Whether this is a rush order"
    )
    
    # Artwork info for validation
    artwork_dpi: Optional[int] = Field(
        default=None,
        description="DPI of provided artwork (for quality validation)"
    )
    
    raw_input: Optional[str] = Field(
        default=None,
        description="Original input text (for audit/debugging)"
    )


class ValidationResult(BaseModel):
    """
    Result of specification validation.
    
    Design Decision: Three-tier feedback system
    - Errors (blockers): Cannot proceed - requires human review
    - Warnings: Can proceed with caution - user should acknowledge
    - Missing fields: Informational - defaults will be used
    
    This helps n8n workflow route orders appropriately.
    """
    
    is_valid: bool = Field(
        description="Whether specs are valid enough to proceed with pricing"
    )
    
    errors: list[str] = Field(
        default_factory=list,
        description="Blocking issues that prevent processing"
    )
    
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking issues or notes for the user"
    )
    
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields that were not extracted (defaults applied)"
    )


class PricingBreakdown(BaseModel):
    """
    Detailed cost breakdown for transparency and audit.
    
    Shows exactly how the final price was calculated.
    This is what the pricing engine produces internally.
    """
    
    # Core costs
    material_cost: float = Field(
        ge=0,
        description="Cost of paper/substrate"
    )
    
    print_cost: float = Field(
        ge=0,
        description="Cost of printing (ink, press time)"
    )
    
    setup_cost: float = Field(
        ge=0,
        description="Setup/plate costs (higher for offset)"
    )
    
    finishing_cost: float = Field(
        ge=0,
        description="Post-press finishing (cutting, coating)"
    )
    
    # Options (individual costs)
    option_costs: dict[str, float] = Field(
        default_factory=dict,
        description="Cost per additional option"
    )
    
    # Adjustments
    rush_fee: float = Field(
        default=0.0,
        description="Rush order surcharge"
    )
    
    quantity_discount: float = Field(
        default=0.0,
        description="Volume discount (negative value)"
    )
    
    # Margin
    margin_amount: float = Field(
        ge=0,
        description="Business margin applied"
    )
    
    margin_percent: float = Field(
        ge=0,
        description="Margin percentage for reference"
    )


class PriceEstimate(BaseModel):
    """
    Complete price estimate for print job.
    
    Includes:
    - Full pricing breakdown
    - Print method decision (digital vs offset)
    - Total calculation
    
    Design Decision: All prices in USD, tax calculated separately
    """
    
    # Method decision (critical for assessment)
    print_method: Literal["digital", "offset"] = Field(
        description="Selected print method based on quantity and specs"
    )
    
    print_method_reason: str = Field(
        default="",
        description="Explanation for print method choice"
    )
    
    # Detailed breakdown
    breakdown: PricingBreakdown = Field(
        description="Detailed cost breakdown"
    )
    
    # Totals (convenience fields)
    subtotal: float = Field(
        ge=0,
        description="Sum before tax"
    )
    
    tax: float = Field(
        default=0.0,
        description="Estimated tax amount"
    )
    
    total: float = Field(
        ge=0,
        description="Final total including tax"
    )
    
    currency: str = Field(
        default="USD",
        description="Currency code"
    )
    
    # Estimate metadata
    estimate_notes: list[str] = Field(
        default_factory=list,
        description="Additional notes about the estimate"
    )
    
    # TODO: Add estimated delivery date calculation
    # estimated_delivery: Optional[date] = None
