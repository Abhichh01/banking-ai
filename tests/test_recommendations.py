""
Tests for the recommendations endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.core.llm_orchestrator import LLMOrchestrator, LLMResponse

client = TestClient(app)

@pytest.fixture
def mock_llm_orchestrator():
    with patch('app.api.v1.endpoints.recommendations.LLMOrchestrator') as mock:
        mock.return_value.process_request.return_value = LLMResponse(
            content="Sample recommendations response",
            model_used="claude-3-sonnet-20240229",
            tokens_used=150,
            processing_time=0.7
        )
        yield mock

@pytest.fixture
def mock_memory_manager():
    with patch('app.api.v1.endpoints.recommendations.MemoryManager') as mock:
        yield mock

def test_generate_recommendations_success(mock_llm_orchestrator, mock_memory_manager):
    """Test successful generation of financial recommendations."""
    test_data = {
        "customer_id": "cust_123",
        "goals": [
            {
                "id": "goal_1",
                "name": "Buy a house",
                "target_amount": 500000,
                "current_amount": 50000,
                "target_date": "2030-01-01",
                "priority": "high"
            }
        ],
        "risk_tolerance": "moderate",
        "time_horizon": "5y",
        "include_products": True
    }
    
    response = client.post("/api/v1/recommendations/generate", json=test_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_123"
    assert data["time_horizon"] == "5y"
    assert data["risk_tolerance"] == "moderate"
    assert len(data["recommendations"]) > 0
    assert data["summary"] is not None

def test_get_recommended_products():
    """Test retrieval of recommended financial products."""
    # Test with no filters
    response = client.get("/api/v1/recommendations/products?customer_id=cust_123")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    
    # Test with product type filter
    response = client.get("/api/v1/recommendations/products?customer_id=cust_123&product_type=savings")
    assert response.status_code == 200
    savings_products = response.json()
    assert all(p["type"] == "savings" for p in savings_products)
    
    # Test with risk level filter
    response = client.get("/api/v1/recommendations/products?customer_id=cust_123&risk_level=low")
    assert response.status_code == 200
    low_risk_products = response.json()
    assert all(p["risk_level"] == "low" for p in low_risk_products)

def test_generate_recommendations_invalid_goal():
    """Test recommendations with invalid goal data."""
    invalid_data = {
        "customer_id": "cust_123",
        "goals": [
            {
                "id": "goal_1",
                "name": "Invalid goal",
                "target_amount": -100,  # Invalid amount
                "current_amount": 0,
                "target_date": "2020-01-01"  # Past date
            }
        ]
    }
    
    response = client.post("/api/v1/recommendations/generate", json=invalid_data)
    assert response.status_code == 422  # Validation error
