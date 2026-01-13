"""
Specification Validation Service

Validates extracted print specifications against business rules.

╔═══════════════════════════════════════════════════════════════════════════╗
║  VALIDATION PHILOSOPHY                                                     ║
║                                                                             ║
║  Three-tier feedback system enables SMART WORKFLOW ROUTING:               ║
║                                                                             ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  ERRORS (Blockers)    → Order cannot proceed automatically          │  ║
║  │                       → Routes to CSR review queue                   │  ║
║  │                       → Human intervention required                  │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │  WARNINGS             → Order can proceed with acknowledgment       │  ║
║  │                       → Routes to customer confirmation step        │  ║
║  │                       → Automated email/SMS for consent             │  ║
║  ├─────────────────────────────────────────────────────────────────────┤  ║
║  │  MISSING FIELDS       → Defaults applied automatically              │  ║
║  │                       → Routes to auto-approve path                 │  ║
║  │                       → Fastest fulfillment                         │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                             ║
║  This categorization drives n8n workflow routing decisions.               ║
╚═══════════════════════════════════════════════════════════════════════════╝

Design Decisions:
1. Validation is SEPARATE from extraction (single responsibility)
2. Return ALL issues, not just the first (better UX, complete feedback)
3. Distinct error types enable smart workflow routing
4. Business rules are explicit and documented
5. NO AI/LLM - rules are deterministic and auditable
"""

import logging
from typing import Optional

from app.schemas.print_specs import PrintSpecs, ValidationResult

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# ── Valid Product Types (Whitelist Approach) ─────────────────────────────
# Only these product types are accepted. Unknown types are rejected.
# This prevents pricing errors from unsupported products.
VALID_PRODUCT_TYPES = {
    "business_cards",
    "flyers",
    "posters",
    "brochures",
    "booklets",
    "stickers",
    "banners",
    "postcards",
    "letterhead",
    "envelopes",
    "folders",
    "notepads",
    "catalogs",
    "magazines",
}

# ── Valid Finishing Options ──────────────────────────────────────────────
# Options that have pricing rules. Unknown options are flagged.
VALID_OPTIONS = {
    "rounded_corners",
    "foil_stamping",
    "embossing",
    "spot_uv",
    "die_cut",
    "hole_punch",
    "scoring",
    "perforation",
    "lamination",
    "uv_coating",
}

# ── Quantity Limits by Product Type ──────────────────────────────────────
# Minimum: Prevents unprofitable small orders
# Maximum: Prevents unrealistic orders (likely typos or attacks)
QUANTITY_LIMITS = {
    "business_cards": {"min": 100, "max": 100000},   # Standard minimums
    "flyers": {"min": 50, "max": 500000},
    "posters": {"min": 1, "max": 10000},              # Can order single posters
    "brochures": {"min": 50, "max": 100000},
    "booklets": {"min": 25, "max": 50000},
    "stickers": {"min": 50, "max": 500000},
    "banners": {"min": 1, "max": 500},                # Low max (large items)
    "postcards": {"min": 100, "max": 500000},
    "default": {"min": 1, "max": 100000},
}

# ── Standard Sizes by Product Type ───────────────────────────────────────
# Non-standard sizes get WARNING (not error) - they're allowed but flagged
# Custom sizes may affect pricing and require manual quote
STANDARD_SIZES = {
    "business_cards": ["3.5x2", "2x3.5", "3x3"],
    "flyers": ["8.5x11", "5.5x8.5", "4x6", "11x17"],
    "posters": ["11x17", "18x24", "24x36"],
    "postcards": ["4x6", "5x7", "6x9"],
}

# ── Artwork Quality Thresholds ───────────────────────────────────────────
# DPI (dots per inch) requirements for print quality
# Below 200: Unprintable (pixelated) → ERROR
# 200-300: Acceptable but not ideal → WARNING
# 300+: Professional print quality → OK
MIN_PRINT_DPI = 300      # Recommended for quality output
WARN_DPI_THRESHOLD = 200  # Below this is too low quality


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def validate_specs(specs: Optional[PrintSpecs]) -> ValidationResult:
    """
    Validate extracted print specifications against business rules.
    
    ┌─────────────────────────────────────────────────────────────────────┐
    │  CHECKS PERFORMED (in order)                                        │
    │                                                                     │
    │  1. Required Fields: product_type, quantity                         │
    │  2. Product Type: Must be in whitelist                              │
    │  3. Quantity Range: Within min/max for product type                 │
    │  4. Size: Standard vs custom (warning for custom)                   │
    │  5. Artwork DPI: Quality check if provided                          │
    │  6. Turnaround: Feasibility check, rush conflicts                   │
    │  7. Options: Compatibility checks                                   │
    │  8. Business Rules: Large order notifications                       │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        specs: Extracted print specifications (may be None or partial)
        
    Returns:
        ValidationResult with is_valid flag, errors, warnings, missing_fields
        
    Design Decision:
        Return ALL issues found, not just the first one.
        This gives users complete feedback in one request.
    """
    errors: list[str] = []        # Blockers - order cannot proceed
    warnings: list[str] = []       # Cautions - needs acknowledgment
    missing_fields: list[str] = [] # Informational - defaults applied
    
    # ══════════════════════════════════════════════════════════════════════
    # NULL SPECS CHECK
    # Complete extraction failure - nothing to validate
    # ══════════════════════════════════════════════════════════════════════
    if specs is None:
        return ValidationResult(
            is_valid=False,
            errors=["No specifications could be extracted from input"],
            warnings=[],
            missing_fields=[]
        )
    
    # ══════════════════════════════════════════════════════════════════════
    # PRODUCT TYPE VALIDATION (REQUIRED)
    # Must be present and in whitelist
    # ══════════════════════════════════════════════════════════════════════
    if not specs.product_type:
        errors.append(
            "Product type is required. "
            "Examples: business_cards, flyers, posters, brochures"
        )
    elif specs.product_type not in VALID_PRODUCT_TYPES:
        # Unknown product type - could be typo or unsupported product
        errors.append(
            f"Unknown product type '{specs.product_type}'. "
            f"Valid types: {', '.join(sorted(VALID_PRODUCT_TYPES))}"
        )
    
    # ══════════════════════════════════════════════════════════════════════
    # QUANTITY VALIDATION (REQUIRED)
    # Must be positive and within product-specific limits
    # ══════════════════════════════════════════════════════════════════════
    if specs.quantity is None:
        errors.append("Quantity is required")
    elif specs.quantity <= 0:
        errors.append("Quantity must be a positive number")
    else:
        # Check product-specific quantity limits
        limits = QUANTITY_LIMITS.get(
            specs.product_type or "default", 
            QUANTITY_LIMITS["default"]
        )
        
        if specs.quantity < limits["min"]:
            # Below minimum - not profitable for the business
            errors.append(
                f"Minimum quantity for {specs.product_type} is {limits['min']} units"
            )
        elif specs.quantity > limits["max"]:
            # Above maximum - likely error or needs custom quote
            errors.append(
                f"Maximum quantity for {specs.product_type} is {limits['max']:,}. "
                "Contact sales for bulk orders."
            )
    
    # ══════════════════════════════════════════════════════════════════════
    # SIZE VALIDATION
    # Missing: Use default (warning)
    # Non-standard: Allow but warn (may affect price)
    # ══════════════════════════════════════════════════════════════════════
    if not specs.size:
        missing_fields.append("size")
        warnings.append("Size not specified - using standard size for product type")
    elif specs.product_type and specs.product_type in STANDARD_SIZES:
        standard = STANDARD_SIZES[specs.product_type]
        if specs.size not in standard:
            # Non-standard size - allowed but flagged
            warnings.append(
                f"Non-standard size '{specs.size}' for {specs.product_type}. "
                f"Standard sizes: {', '.join(standard)}. Custom sizing may affect price."
            )
    
    # ══════════════════════════════════════════════════════════════════════
    # ARTWORK QUALITY VALIDATION (IF DPI PROVIDED)
    # Below 200 DPI: Unprintable quality → ERROR
    # 200-300 DPI: Acceptable but suboptimal → WARNING
    # 300+ DPI: Professional quality → OK
    # ══════════════════════════════════════════════════════════════════════
    if specs.artwork_dpi is not None:
        if specs.artwork_dpi < WARN_DPI_THRESHOLD:
            # Too low - will produce pixelated/blurry prints
            errors.append(
                f"Artwork resolution too low ({specs.artwork_dpi} DPI). "
                f"Minimum {MIN_PRINT_DPI} DPI required for print quality. "
                "Please provide higher resolution artwork."
            )
        elif specs.artwork_dpi < MIN_PRINT_DPI:
            # Acceptable but not ideal
            warnings.append(
                f"Artwork resolution ({specs.artwork_dpi} DPI) is below recommended "
                f"{MIN_PRINT_DPI} DPI. Print quality may be affected."
            )
    
    # ══════════════════════════════════════════════════════════════════════
    # TURNAROUND / RUSH VALIDATION
    # Check for feasibility and conflicts with slow-process options
    # ══════════════════════════════════════════════════════════════════════
    if specs.turnaround_days is not None:
        if specs.turnaround_days < 0:
            errors.append("Turnaround days cannot be negative")
        elif specs.turnaround_days == 0:
            # Same-day - possible but expensive
            warnings.append(
                "Same-day turnaround requested. "
                "Subject to availability and rush fees apply."
            )
        elif specs.turnaround_days <= 2:
            # Rush order - standard rush fee
            warnings.append(
                f"{specs.turnaround_days}-day rush turnaround. Rush fees will apply."
            )
        
        # ── Conflict Check: Rush + Slow Options ────────────────────────────
        # Some finishing options (foil, embossing, die-cut) require 5+ days
        # Rush turnaround is incompatible with these
        if specs.turnaround_days <= 2 and specs.options:
            slow_options = {"foil_stamping", "embossing", "die_cut"}
            conflicting = set(specs.options) & slow_options
            if conflicting:
                errors.append(
                    f"Rush turnaround conflicts with options: {', '.join(conflicting)}. "
                    f"These options require 5+ business days."
                )
    
    # ══════════════════════════════════════════════════════════════════════
    # OPTIONS VALIDATION
    # Unknown options: Warning (will be ignored in pricing)
    # Compatibility conflicts: Warning
    # ══════════════════════════════════════════════════════════════════════
    if specs.options:
        unknown_options = set(specs.options) - VALID_OPTIONS
        if unknown_options:
            # Unknown options - won't be priced, but order can proceed
            warnings.append(
                f"Unknown options will be ignored: {', '.join(sorted(unknown_options))}"
            )
        
        # ── Compatibility Check: Embossing + Lamination ────────────────────
        # Lamination after embossing can flatten the emboss effect
        if "embossing" in specs.options and "lamination" in specs.options:
            warnings.append(
                "Embossing and lamination together may affect emboss visibility"
            )
    
    # ══════════════════════════════════════════════════════════════════════
    # MISSING OPTIONAL FIELDS
    # Track what defaults will be applied
    # ══════════════════════════════════════════════════════════════════════
    if not specs.sides:
        missing_fields.append("sides")
        warnings.append("Sides not specified - defaulting to single-sided")
    
    if not specs.finish:
        missing_fields.append("finish")
        warnings.append("Finish not specified - defaulting to matte")
    
    if not specs.color_mode:
        missing_fields.append("color_mode")
        warnings.append("Color mode not specified - assuming full color")
    
    if not specs.paper_stock:
        missing_fields.append("paper_stock")
        # Not a warning - we'll silently use product default
    
    # ══════════════════════════════════════════════════════════════════════
    # BUSINESS RULE WARNINGS
    # Informational notices that don't block the order
    # ══════════════════════════════════════════════════════════════════════
    
    # Large order notification - may qualify for custom quote
    if specs.quantity and specs.quantity >= 5000:
        warnings.append(
            "Large order: may qualify for additional volume discounts. "
            "Contact sales for custom quote."
        )
    
    # Specialty finish timeline warning
    if specs.options and ("foil_stamping" in specs.options or "embossing" in specs.options):
        warnings.append(
            "Specialty finishes (foil/emboss) add 5-7 business days to production"
        )
    
    # ══════════════════════════════════════════════════════════════════════
    # DETERMINE OVERALL VALIDITY
    # Valid = no errors (warnings are OK, missing fields are OK)
    # ══════════════════════════════════════════════════════════════════════
    is_valid = len(errors) == 0
    
    logger.info(
        f"Validation: valid={is_valid}, "
        f"errors={len(errors)}, warnings={len(warnings)}, "
        f"missing={len(missing_fields)}"
    )
    
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        missing_fields=missing_fields
    )
