"""
Tests for the /intake endpoint.

Tests cover:
1. Successful text extraction and pricing
2. Validation error handling
3. Missing required fields
4. Edge cases

Run with: pytest tests/test_intake.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.print_specs import PrintSpecs


client = TestClient(app)


class TestIntakeEndpoint:
    """Tests for POST /intake endpoint."""
    
    @patch("app.routers.intake.extract_print_specs")
    def test_successful_text_intake(self, mock_extract):
        """
        Test successful extraction from text input.
        
        Given: Valid text describing a print job
        When: POST to /intake
        Then: Returns success with specs and estimate
        """
        # Arrange: Mock LLM extraction
        mock_extract.return_value = PrintSpecs(
            product_type="business_cards",
            quantity=500,
            sides="double",
            finish="matte",
            options=["rounded_corners"]
        )
        
        # Act
        response = client.post("/intake", json={
            "input_type": "text",
            "content": "500 business cards, double-sided, matte with rounded corners"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["extracted_specs"]["product_type"] == "business_cards"
        assert data["extracted_specs"]["quantity"] == 500
        assert data["validation"]["is_valid"] is True
        assert data["estimate"]["total"] > 0
    
    @patch("app.routers.intake.extract_print_specs")
    def test_validation_errors(self, mock_extract):
        """
        Test handling of invalid specifications.
        
        Given: Extracted specs with unknown product type
        When: POST to /intake
        Then: Returns validation_errors status with error details
        """
        # Arrange: Mock extraction with invalid product
        mock_extract.return_value = PrintSpecs(
            product_type="unknown_product",
            quantity=100
        )
        
        # Act
        response = client.post("/intake", json={
            "input_type": "text",
            "content": "100 unknown products"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "validation_errors"
        assert data["validation"]["is_valid"] is False
        assert len(data["validation"]["errors"]) > 0
        assert "unknown_product" in data["validation"]["errors"][0].lower()
    
    @patch("app.routers.intake.extract_print_specs")
    def test_missing_quantity(self, mock_extract):
        """
        Test handling of missing required field.
        
        Given: Extracted specs without quantity
        When: POST to /intake  
        Then: Returns validation error about missing quantity
        """
        # Arrange
        mock_extract.return_value = PrintSpecs(
            product_type="flyers"
            # quantity is None
        )
        
        # Act
        response = client.post("/intake", json={
            "input_type": "text",
            "content": "some flyers"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["validation"]["is_valid"] is False
        assert any("quantity" in e.lower() for e in data["validation"]["errors"])
    
    @patch("app.routers.intake.extract_print_specs")
    def test_extraction_failure(self, mock_extract):
        """
        Test graceful handling of LLM extraction failure.
        
        Given: LLM extraction throws an error
        When: POST to /intake
        Then: Returns extraction_failed status with error message
        """
        # Arrange: Mock extraction failure
        mock_extract.side_effect = Exception("LLM API unavailable")
        
        # Act
        response = client.post("/intake", json={
            "input_type": "text",
            "content": "500 business cards"
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "extraction_failed"
        assert data["extracted_specs"] is None
        assert "extract" in data["validation"]["errors"][0].lower()
    
    def test_empty_content(self):
        """
        Test handling of empty content.
        
        Given: Text input with no content
        When: POST to /intake
        Then: Request is accepted (validation happens after extraction)
        """
        response = client.post("/intake", json={
            "input_type": "text",
            "content": ""
        })
        
        # Should still return 200 (we handle this gracefully)
        assert response.status_code == 200
    
    def test_pdf_metadata_input(self):
        """
        Test handling of PDF metadata input.
        
        Given: PDF input type with metadata
        When: POST to /intake
        Then: Request is processed (actual PDF parsing is stubbed)
        """
        response = client.post("/intake", json={
            "input_type": "pdf",
            "metadata": {
                "filename": "specs.pdf",
                "pages": 2
            }
        })
        
        # Should return 200 even though actual parsing is TODO
        assert response.status_code == 200


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""
    
    def test_health_check(self):
        """
        Test health check returns healthy status.
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
