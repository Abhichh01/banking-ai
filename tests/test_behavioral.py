""
Tests for the behavioral analysis endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.llm_orchestrator import LLMOrchestrator, LLMResponse

client = TestClient(app)

@pytest.fixture
def mock_llm_orchestrator():
    with patch('app.api.v1.endpoints.behavioral.LLMOrchestrator') as mock:
        mock.return_value.process_request.return_value = LLMResponse(
            content="Sample analysis response",
            model_used="gpt-4o",
            tokens_used=100,
            processing_time=0.5
        )
        yield mock

@pytest.fixture
def mock_memory_manager():
    with patch('app.api.v1.endpoints.behavioral.MemoryManager') as mock:
        yield mock

def test_analyze_behavior_success(mock_llm_orchestrator, mock_memory_manager):
    """Test successful behavioral analysis request."""
    test_data = {
        "customer_id": "cust_123",
        "transactions": [
            {
                "id": "txn_1",
                "amount": 100.0,
                "date": "2023-01-01",
                "category": "groceries",
                "description": "Grocery store",
                "type": "debit"
            },
            {
                "id": "txn_2",
                "amount": 2000.0,
                "date": "2023-01-02",
                "category": "income",
                "description": "Monthly salary",
                "type": "credit"
            }
        ],
        "time_period": "30d",
        "include_insights": True,
        "include_recommendations": True
    }
    
    response = client.post("/api/v1/behavioral/analyze", json=test_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_123"
    assert data["time_period"] == "30d"
    assert data["total_transactions"] == 2
    assert data["total_spent"] == 100.0
    assert data["total_income"] == 2000.0
    assert len(data["behavioral_insights"]) > 0
    assert data["recommendations"] is not None

def test_analyze_behavior_invalid_data():
    """Test behavioral analysis with invalid data."""
    invalid_data = {
        "customer_id": "cust_123",
        "transactions": [
            {
                "id": "txn_1",
                "amount": "not_a_number",  # Invalid type
                "date": "2023-01-01",
                "category": "groceries",
                "description": "Grocery store",
                "type": "debit"
            }
        ]
    }
    
    response = client.post("/api/v1/behavioral/analyze", json=invalid_data)
    assert response.status_code == 422  # Validation error

def test_analyze_behavior_empty_transactions():
    """Test behavioral analysis with empty transactions list."""
    test_data = {
        "customer_id": "cust_123",
        "transactions": []
    }
    
    response = client.post("/api/v1/behavioral/analyze", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 0
    assert data["total_spent"] == 0
    assert data["total_income"] == 0
