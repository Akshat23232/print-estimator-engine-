"""
Rule-Based Pricing Engine

Calculates print job pricing using DETERMINISTIC rules from JSON configuration.

╔═══════════════════════════════════════════════════════════════════════════╗
║  IMPORTANT: NO AI/LLM IS USED IN THIS MODULE                               ║
║                                                                             ║
║  All pricing is calculated using explicit rules and formulas.              ║
║  This is intentional - pricing must be auditable and predictable.          ║
║                                                                             ║
║  Why deterministic pricing matters:                                        ║
║  1. Same input MUST produce same output (reproducibility)                  ║
║  2. Every line item can be traced to a rule (auditability)                 ║
║  3. Customers can verify calculations (transparency)                       ║
║  4. Legal disputes require clear calculation trail (compliance)            ║
╚═══════════════════════════════════════════════════════════════════════════╝

Design Decisions:
1. Configuration-driven: All rates in pricing.json (version controlled)
2. Print method decision: Digital vs Offset based on quantity thresholds
3. Transparent breakdown: Every cost component itemized
4. Deterministic: Same input = same output (no ML/AI)
5. Minimum price enforcement: Small orders have floor price

Pricing Formula:
    base = material_cost + print_cost + setup_cost + finishing_cost
    options = sum of applicable option costs
    adjustments = quantity_discount + rush_fee
    margin = (base + options + adjustments) * margin_rate
    total = base + options + adjustments + margin + tax
"""

import json
import logging
from pathlib import Path
from functools import lru_cache
from typing import Optional, Literal

from app.config import get_settings
from app.schemas.print_specs import PrintSpecs, PriceEstimate, PricingBreakdown

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

@lru_cache(maxsize=1)
def load_pricing_config() -> dict:
    """
    Load and cache pricing configuration.
    
    Design Decisions:
    - Cached: Config rarely changes, and we want fast pricing calculations
    - JSON file: Easy to audit, version control, and modify without deploys
    - Fallback: Default config if file not found (graceful degradation)
    
    TODO: In production, consider:
    - Database-backed pricing with admin UI
    - Cache invalidation webhook for config updates
    - A/B testing support for pricing experiments
    """
    settings = get_settings()
    config_path = Path(__file__).parent.parent / settings.pricing_config_path
    
    try:
        with open(config_path) as f:
            config = json.load(f)
            logger.info(f"Loaded pricing config from {config_path}")
            return config
    except FileNotFoundError:
        logger.warning(f"Pricing config not found at {config_path}, using defaults")
        return get_default_pricing_config()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid pricing config JSON: {e}")
        return get_default_pricing_config()


def get_default_pricing_config() -> dict:
    """
    Fallback pricing configuration with realistic industry rates.
    
    Used when pricing.json is not found or invalid.
    All values are USD and based on typical commercial printing rates.
    """
    return {
        # ══════════════════════════════════════════════════════════════════
        # PRODUCT BASE RATES
        # Per-unit costs for material, printing, and finishing
        # ══════════════════════════════════════════════════════════════════
        "products": {
            "business_cards": {
                "material_per_unit": 0.02,    # Cardstock cost
                "print_per_unit": 0.04,       # Ink/press time
                "finishing_per_unit": 0.02,   # Cutting, packaging
                "minimum_quantity": 100,
                "minimum_price": 29.99,
                "default_size": "3.5x2"
            },
            "flyers": {
                "material_per_unit": 0.03,
                "print_per_unit": 0.08,
                "finishing_per_unit": 0.02,
                "minimum_quantity": 50,
                "minimum_price": 35.00,
                "default_size": "8.5x11"
            },
            "brochures": {
                "material_per_unit": 0.08,
                "print_per_unit": 0.15,
                "finishing_per_unit": 0.05,   # Includes folding
                "minimum_quantity": 50,
                "minimum_price": 75.00,
                "default_size": "8.5x11"
            },
            "posters": {
                "material_per_unit": 0.25,
                "print_per_unit": 0.50,
                "finishing_per_unit": 0.10,
                "minimum_quantity": 1,
                "minimum_price": 15.00,
                "default_size": "18x24"
            },
            "postcards": {
                "material_per_unit": 0.03,
                "print_per_unit": 0.05,
                "finishing_per_unit": 0.02,
                "minimum_quantity": 100,
                "minimum_price": 30.00,
                "default_size": "4x6"
            },
            "default": {
                "material_per_unit": 0.05,
                "print_per_unit": 0.10,
                "finishing_per_unit": 0.03,
                "minimum_quantity": 1,
                "minimum_price": 25.00,
                "default_size": "8.5x11"
            }
        },
        
        # ══════════════════════════════════════════════════════════════════
        # PRINT METHOD THRESHOLDS
        # 
        # Industry standard break-even analysis:
        # - Digital: Lower setup ($15), higher per-unit cost
        # - Offset: Higher setup ($150), lower per-unit cost (0.6x multiplier)
        #
        # The 500-unit threshold is where offset becomes cost-effective:
        # At 499 units: Digital = $15 setup, Offset = $150 setup → Digital wins
        # At 500 units: Per-unit savings offset the setup cost difference
        # ══════════════════════════════════════════════════════════════════
        "print_method": {
            "digital": {
                "setup_cost": 15.00,          # No plates needed
                "cost_multiplier": 1.0,       # Base rate
                "max_efficient_quantity": 500
            },
            "offset": {
                "setup_cost": 150.00,         # Plate production cost
                "cost_multiplier": 0.6,       # 40% cheaper per unit at scale
                "min_efficient_quantity": 500
            },
            "threshold_quantity": 500         # Switch point (configurable)
        },
        
        # ══════════════════════════════════════════════════════════════════
        # FINISHING OPTIONS
        # Type determines pricing model:
        # - "flat": Fixed fee regardless of quantity (setup-based)
        # - "per_unit": Multiplied by quantity (labor-based)
        # ══════════════════════════════════════════════════════════════════
        "options": {
            "rounded_corners": {"price": 15.00, "type": "flat"},      # Die setup
            "foil_stamping": {"price": 0.08, "type": "per_unit"},     # Per-piece
            "embossing": {"price": 0.10, "type": "per_unit"},         # Per-piece
            "spot_uv": {"price": 25.00, "type": "flat"},              # Plate setup
            "die_cut": {"price": 75.00, "type": "flat"},              # Custom die
            "lamination": {"price": 0.03, "type": "per_unit"},        # Per-piece
            "uv_coating": {"price": 0.02, "type": "per_unit"},        # Per-piece
            "hole_punch": {"price": 10.00, "type": "flat"},           # Setup only
            "scoring": {"price": 0.01, "type": "per_unit"},           # Per-piece
            "perforation": {"price": 0.02, "type": "per_unit"}        # Per-piece
        },
        
        # ══════════════════════════════════════════════════════════════════
        # MODIFIERS
        # Multipliers applied to print and finishing costs
        # Based on ink coverage, press time, and material costs
        # ══════════════════════════════════════════════════════════════════
        "modifiers": {
            "double_sided": 1.6,      # 60% more (not 2x due to setup efficiency)
            "full_color": 1.0,        # Base rate (CMYK)
            "black_white": 0.5,       # 50% cheaper (1 ink vs 4)
            "spot_color": 0.75,       # 25% cheaper than full color
            "gloss_finish": 1.1,      # Coating cost
            "matte_finish": 1.0,      # Base finish
            "satin_finish": 1.05,     # Slight premium
            "uncoated": 0.9           # No coating = cheaper
        },
        
        # ══════════════════════════════════════════════════════════════════
        # QUANTITY DISCOUNTS
        # Standard volume discount tiers
        # Larger orders = better economies of scale
        # ══════════════════════════════════════════════════════════════════
        "quantity_discounts": [
            {"min_quantity": 250, "discount": 0.05},    # 5% off
            {"min_quantity": 500, "discount": 0.10},    # 10% off
            {"min_quantity": 1000, "discount": 0.15},   # 15% off
            {"min_quantity": 5000, "discount": 0.20},   # 20% off
            {"min_quantity": 10000, "discount": 0.25}   # 25% off (max)
        ],
        
        # ══════════════════════════════════════════════════════════════════
        # RUSH PRICING
        # Surcharges for expedited production
        # Based on overtime labor and priority scheduling
        # ══════════════════════════════════════════════════════════════════
        "rush_pricing": {
            "same_day": 2.0,      # 100% surcharge (premium)
            "next_day": 1.5,      # 50% surcharge
            "2_day": 1.25,        # 25% surcharge
            "standard": 1.0       # No surcharge (5-7 business days)
        },
        
        # ══════════════════════════════════════════════════════════════════
        # BUSINESS MARGIN
        # Standard markup for profitability
        # ══════════════════════════════════════════════════════════════════
        "margin_percent": 0.30,  # 30% margin (industry standard)
        
        # ══════════════════════════════════════════════════════════════════
        # TAX
        # Configurable per jurisdiction
        # ══════════════════════════════════════════════════════════════════
        "tax_rate": 0.0  # Default 0% - configure per location
    }


# ============================================================================
# PRINT METHOD DECISION
# ============================================================================

def determine_print_method(
    quantity: int, 
    config: dict
) -> tuple[Literal["digital", "offset"], str]:
    """
    Determine optimal print method based on quantity.
    
    ┌─────────────────────────────────────────────────────────────────────┐
    │  DECISION LOGIC (Industry Standard)                                 │
    │                                                                     │
    │  DIGITAL PRINTING                    OFFSET PRINTING                │
    │  ─────────────────                   ────────────────               │
    │  • Best for: < 500 units             • Best for: ≥ 500 units        │
    │  • Setup: $15 (no plates)            • Setup: $150 (plate costs)    │
    │  • Per-unit: Higher                  • Per-unit: 40% lower          │
    │  • Turnaround: Faster                • Turnaround: Longer           │
    │  • Variable data: Supported          • Pantone: Exact matching      │
    │                                                                     │
    │  The 500-unit threshold is the break-even point where offset       │
    │  setup cost is recouped by lower per-unit costs.                   │
    └─────────────────────────────────────────────────────────────────────┘
    
    Args:
        quantity: Number of units to print
        config: Pricing configuration dictionary
        
    Returns:
        Tuple of (method, human-readable explanation)
    """
    threshold = config.get("print_method", {}).get("threshold_quantity", 500)
    
    if quantity < threshold:
        return (
            "digital",
            f"Digital printing selected: quantity ({quantity}) below {threshold} threshold. "
            f"Faster turnaround, no plate setup required."
        )
    else:
        return (
            "offset", 
            f"Offset printing selected: quantity ({quantity}) at or above {threshold} threshold. "
            f"Lower per-unit cost at scale, requires plate setup."
        )


# ============================================================================
# MAIN PRICING CALCULATION
# ============================================================================

def calculate_price(specs: PrintSpecs) -> Optional[PriceEstimate]:
    """
    Calculate price estimate for print specifications.
    
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  DETERMINISTIC GUARANTEE                                               ║
    ║                                                                         ║
    ║  Given identical PrintSpecs input, this function will ALWAYS return   ║
    ║  the exact same PriceEstimate. No randomness, no AI, no variability.  ║
    ║                                                                         ║
    ║  This is critical for:                                                 ║
    ║  • Customer trust (consistent pricing)                                 ║
    ║  • Financial auditing (traceable calculations)                         ║
    ║  • Legal compliance (defensible pricing)                               ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    
    Calculation Steps:
    1. Determine print method (digital vs offset based on quantity)
    2. Calculate base costs (material, print, setup, finishing)
    3. Apply modifiers (sides, color mode, finish type)
    4. Add option costs (flat fee or per-unit)
    5. Apply quantity discounts (tiered)
    6. Add rush fees if applicable
    7. Calculate business margin
    8. Apply tax
    9. Enforce minimum price
    
    Args:
        specs: Validated print specifications
        
    Returns:
        PriceEstimate with complete itemized breakdown
    """
    config = load_pricing_config()
    
    # Get product config (fallback to default for unknown products)
    product_type = specs.product_type or "default"
    product_config = config["products"].get(
        product_type, 
        config["products"]["default"]
    )
    
    quantity = specs.quantity or 1
    estimate_notes: list[str] = []
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 1: Determine Print Method
    # This affects setup cost and per-unit print cost
    # ══════════════════════════════════════════════════════════════════════
    print_method, method_reason = determine_print_method(quantity, config)
    method_config = config.get("print_method", {}).get(print_method, {})
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 2: Calculate Base Costs
    # Each component is tracked separately for transparency
    # ══════════════════════════════════════════════════════════════════════
    
    # Material cost: substrate/paper × quantity
    material_cost = product_config["material_per_unit"] * quantity
    
    # Print cost: ink/press × quantity × method multiplier
    # Offset has 0.6x multiplier (40% cheaper per unit at scale)
    base_print_cost = product_config["print_per_unit"] * quantity
    print_multiplier = method_config.get("cost_multiplier", 1.0)
    print_cost = base_print_cost * print_multiplier
    
    # Setup cost: fixed cost based on print method
    # Digital: $15 (direct-to-press), Offset: $150 (plate production)
    setup_cost = method_config.get("setup_cost", 15.00)
    
    # Finishing cost: post-press processing × quantity
    finishing_cost = product_config["finishing_per_unit"] * quantity
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 3: Apply Modifiers
    # Multipliers based on printing complexity
    # ══════════════════════════════════════════════════════════════════════
    modifiers = config.get("modifiers", {})
    modifier_total = 1.0
    
    # Double-sided: 60% more (not 2x due to setup efficiency)
    if specs.sides == "double":
        modifier_total *= modifiers.get("double_sided", 1.6)
        estimate_notes.append("Double-sided printing applied")
    
    # Color mode: B&W is 50% cheaper, spot color is 75% of full color
    if specs.color_mode:
        modifier_total *= modifiers.get(specs.color_mode, 1.0)
    
    # Finish type: gloss costs 10% more, uncoated is 10% less
    if specs.finish:
        finish_key = f"{specs.finish}_finish" if not specs.finish.endswith("_finish") else specs.finish
        modifier_total *= modifiers.get(finish_key, modifiers.get(specs.finish, 1.0))
    
    # Apply modifiers to print and finishing costs (not material or setup)
    print_cost *= modifier_total
    finishing_cost *= modifier_total
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 4: Calculate Option Costs
    # Two pricing models: flat (fixed fee) or per_unit (quantity-based)
    # ══════════════════════════════════════════════════════════════════════
    option_costs: dict[str, float] = {}
    options_config = config.get("options", {})
    
    for option in specs.options:
        if option in options_config:
            opt_config = options_config[option]
            if opt_config["type"] == "flat":
                # Flat fee: same cost regardless of quantity (e.g., die setup)
                option_costs[option] = opt_config["price"]
            elif opt_config["type"] == "per_unit":
                # Per-unit: scales with quantity (e.g., foil stamping)
                option_costs[option] = opt_config["price"] * quantity
        else:
            # Unknown option: log warning, don't price (fail safe)
            logger.warning(f"Unknown option '{option}' - not priced")
            estimate_notes.append(f"Option '{option}' not in pricing catalog")
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 5: Calculate Subtotal Before Discounts
    # ══════════════════════════════════════════════════════════════════════
    base_total = material_cost + print_cost + setup_cost + finishing_cost
    options_total = sum(option_costs.values())
    pre_discount_total = base_total + options_total
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 6: Apply Quantity Discount
    # Tiered discounts encourage larger orders
    # Find the highest applicable tier (sorted descending)
    # ══════════════════════════════════════════════════════════════════════
    quantity_discount = 0.0
    discount_rate = 0.0
    
    for tier in sorted(
        config.get("quantity_discounts", []),
        key=lambda x: x["min_quantity"],
        reverse=True
    ):
        if quantity >= tier["min_quantity"]:
            discount_rate = tier["discount"]
            quantity_discount = -pre_discount_total * discount_rate
            estimate_notes.append(f"{int(discount_rate * 100)}% volume discount applied")
            break
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 7: Apply Rush Fee
    # Surcharges for expedited production
    # Same-day: 100%, Next-day: 50%, 2-day: 25%
    # ══════════════════════════════════════════════════════════════════════
    rush_fee = 0.0
    rush_config = config.get("rush_pricing", {})
    
    if specs.is_rush or (specs.turnaround_days is not None and specs.turnaround_days <= 2):
        if specs.turnaround_days == 0:
            rush_multiplier = rush_config.get("same_day", 2.0)
            rush_type = "Same-day"
        elif specs.turnaround_days == 1:
            rush_multiplier = rush_config.get("next_day", 1.5)
            rush_type = "Next-day"
        elif specs.turnaround_days == 2:
            rush_multiplier = rush_config.get("2_day", 1.25)
            rush_type = "2-day"
        else:
            rush_multiplier = rush_config.get("next_day", 1.5)
            rush_type = "Rush"
        
        # Rush fee is applied after discount
        rush_fee = (pre_discount_total + quantity_discount) * (rush_multiplier - 1)
        estimate_notes.append(f"{rush_type} rush fee applied ({int((rush_multiplier - 1) * 100)}% surcharge)")
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 8: Calculate Business Margin
    # Standard 30% markup for profitability
    # ══════════════════════════════════════════════════════════════════════
    margin_percent = config.get("margin_percent", 0.30)
    cost_subtotal = pre_discount_total + quantity_discount + rush_fee
    margin_amount = cost_subtotal * margin_percent
    
    # ══════════════════════════════════════════════════════════════════════
    # STEP 9: Calculate Final Totals
    # Apply minimum price and tax
    # ══════════════════════════════════════════════════════════════════════
    subtotal = cost_subtotal + margin_amount
    
    # Enforce minimum price (small orders still need to be profitable)
    minimum_price = product_config.get("minimum_price", 25.00)
    if subtotal < minimum_price:
        subtotal = minimum_price
        estimate_notes.append(f"Minimum order price of ${minimum_price:.2f} applied")
    
    # Tax (configure per jurisdiction, default 0%)
    tax_rate = config.get("tax_rate", 0.0)
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    # ══════════════════════════════════════════════════════════════════════
    # BUILD RESPONSE
    # Complete breakdown for transparency and auditability
    # ══════════════════════════════════════════════════════════════════════
    breakdown = PricingBreakdown(
        material_cost=round(material_cost, 2),
        print_cost=round(print_cost, 2),
        setup_cost=round(setup_cost, 2),
        finishing_cost=round(finishing_cost, 2),
        option_costs={k: round(v, 2) for k, v in option_costs.items()},
        rush_fee=round(rush_fee, 2),
        quantity_discount=round(quantity_discount, 2),
        margin_amount=round(margin_amount, 2),
        margin_percent=margin_percent * 100
    )
    
    return PriceEstimate(
        print_method=print_method,
        print_method_reason=method_reason,
        breakdown=breakdown,
        subtotal=round(subtotal, 2),
        tax=round(tax, 2),
        total=round(total, 2),
        currency="USD",
        estimate_notes=estimate_notes
    )
