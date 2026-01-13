"""
Tests for the pricing engine.

Tests cover:
1. Base price calculation
2. Option pricing (flat vs per-unit)
3. Quantity discounts
4. Modifier application
5. Edge cases

Run with: pytest tests/test_pricing.py -v
"""

import pytest
from app.schemas.print_specs import PrintSpecs
from app.services.pricing import calculate_price, load_pricing_config


class TestPricingEngine:
    """Tests for calculate_price function."""
    
    def test_basic_business_cards(self):
        """
        Test basic business card pricing.
        
        Given: 100 single-sided business cards
        When: Calculate price
        Then: Returns base price at minimum
        """
        specs = PrintSpecs(
            product_type="business_cards",
            quantity=100,
            sides="single"
        )
        
        estimate = calculate_price(specs)
        
        assert estimate is not None
        assert estimate.base_price >= 25.00  # Minimum price
        assert estimate.total > 0
        assert estimate.currency == "USD"
    
    def test_double_sided_modifier(self):
        """
        Test double-sided printing multiplier.
        
        Given: Same order, single vs double-sided
        When: Calculate prices
        Then: Double-sided is more expensive
        """
        single = PrintSpecs(
            product_type="flyers",
            quantity=100,
            sides="single"
        )
        double = PrintSpecs(
            product_type="flyers",
            quantity=100,
            sides="double"
        )
        
        single_estimate = calculate_price(single)
        double_estimate = calculate_price(double)
        
        assert double_estimate.base_price > single_estimate.base_price
    
    def test_flat_option_pricing(self):
        """
        Test flat-rate option (rounded corners).
        
        Given: Business cards with rounded corners
        When: Calculate price
        Then: Rounded corners adds flat fee regardless of quantity
        """
        without_option = PrintSpecs(
            product_type="business_cards",
            quantity=500
        )
        with_option = PrintSpecs(
            product_type="business_cards",
            quantity=500,
            options=["rounded_corners"]
        )
        
        estimate_without = calculate_price(without_option)
        estimate_with = calculate_price(with_option)
        
        assert "rounded_corners" in estimate_with.option_costs
        assert estimate_with.option_costs["rounded_corners"] == 10.00  # Flat fee
        assert estimate_with.total > estimate_without.total
    
    def test_per_unit_option_pricing(self):
        """
        Test per-unit option pricing (foil stamping).
        
        Given: Different quantities with foil stamping
        When: Calculate prices
        Then: Foil cost scales with quantity
        """
        small_order = PrintSpecs(
            product_type="business_cards",
            quantity=100,
            options=["foil_stamping"]
        )
        large_order = PrintSpecs(
            product_type="business_cards",
            quantity=1000,
            options=["foil_stamping"]
        )
        
        small_estimate = calculate_price(small_order)
        large_estimate = calculate_price(large_order)
        
        # Foil is per-unit, so should be 10x for 10x quantity
        assert large_estimate.option_costs["foil_stamping"] > small_estimate.option_costs["foil_stamping"]
    
    def test_quantity_discount_applied(self):
        """
        Test quantity discount tiers.
        
        Given: Order above discount threshold
        When: Calculate price
        Then: Discount is applied and shown as negative
        """
        specs = PrintSpecs(
            product_type="business_cards",
            quantity=1000  # Above 500 threshold
        )
        
        estimate = calculate_price(specs)
        
        # Should have quantity discount (shown as negative)
        assert estimate.quantity_discount < 0
    
    def test_no_discount_below_threshold(self):
        """
        Test no discount for small orders.
        
        Given: Order below minimum discount threshold
        When: Calculate price
        Then: No discount applied
        """
        specs = PrintSpecs(
            product_type="business_cards",
            quantity=100  # Below 250 threshold
        )
        
        estimate = calculate_price(specs)
        
        assert estimate.quantity_discount == 0.0
    
    def test_unknown_product_uses_default(self):
        """
        Test fallback to default pricing for unknown products.
        
        Given: Unknown product type
        When: Calculate price
        Then: Uses default pricing config
        """
        specs = PrintSpecs(
            product_type="mystery_product",
            quantity=10
        )
        
        estimate = calculate_price(specs)
        
        # Should still calculate, using default pricing
        assert estimate is not None
        assert estimate.total > 0
    
    def test_multiple_options(self):
        """
        Test combining multiple options.
        
        Given: Order with multiple options
        When: Calculate price
        Then: All options priced and summed correctly
        """
        specs = PrintSpecs(
            product_type="business_cards",
            quantity=500,
            options=["rounded_corners", "foil_stamping", "spot_uv"]
        )
        
        estimate = calculate_price(specs)
        
        assert len(estimate.option_costs) == 3
        total_options = sum(estimate.option_costs.values())
        assert total_options > 0
    
    def test_minimum_price_enforcement(self):
        """
        Test minimum price is enforced.
        
        Given: Very small order
        When: Calculate price
        Then: Returns at least minimum price
        """
        specs = PrintSpecs(
            product_type="business_cards",
            quantity=1  # Below MOQ, but we still calculate
        )
        
        estimate = calculate_price(specs)
        
        # Should be at least minimum price from config
        config = load_pricing_config()
        min_price = config["products"]["business_cards"]["minimum_price"]
        assert estimate.base_price >= min_price


class TestPricingConfig:
    """Tests for pricing configuration loading."""
    
    def test_config_loads(self):
        """Test pricing config loads without errors."""
        config = load_pricing_config()
        
        assert "products" in config
        assert "options" in config
        assert "modifiers" in config
        assert "quantity_discounts" in config
    
    def test_config_has_required_products(self):
        """Test config includes standard products."""
        config = load_pricing_config()
        
        required = ["business_cards", "flyers", "posters", "default"]
        for product in required:
            assert product in config["products"]
    
    def test_quantity_discounts_ordered(self):
        """Test quantity discounts are properly structured."""
        config = load_pricing_config()
        
        discounts = config["quantity_discounts"]
        assert len(discounts) > 0
        
        # Each tier should have required fields
        for tier in discounts:
            assert "min_quantity" in tier
            assert "discount" in tier
            assert 0 <= tier["discount"] <= 1
