"""
Pytest configuration and fixtures.

Provides shared test fixtures and configuration.
"""

import pytest
import os

# Set test environment variables before importing app
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def sample_business_card_specs():
    """Fixture providing sample business card specifications."""
    from app.schemas.print_specs import PrintSpecs
    
    return PrintSpecs(
        product_type="business_cards",
        quantity=500,
        size="3.5x2",
        paper_stock="14pt",
        sides="double",
        finish="matte",
        color_mode="full_color",
        options=["rounded_corners"]
    )


@pytest.fixture
def sample_flyer_specs():
    """Fixture providing sample flyer specifications."""
    from app.schemas.print_specs import PrintSpecs
    
    return PrintSpecs(
        product_type="flyers",
        quantity=1000,
        size="8.5x11",
        sides="single",
        finish="gloss",
        color_mode="full_color"
    )


@pytest.fixture
def minimal_specs():
    """Fixture providing minimal valid specifications."""
    from app.schemas.print_specs import PrintSpecs
    
    return PrintSpecs(
        product_type="business_cards",
        quantity=100
    )


@pytest.fixture
def invalid_specs():
    """Fixture providing invalid specifications for testing validation."""
    from app.schemas.print_specs import PrintSpecs
    
    return PrintSpecs(
        product_type="unknown_product",
        quantity=-1
    )
