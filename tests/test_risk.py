""
Tests for the risk assessment endpoint.
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
    with patch('app.api.v1.endpoints.risk.LLMOrchestrator') as mock:
        mock.return_value.process_request.return_value = LLMResponse(
            content="Sample risk assessment response",
            model_used="gpt-4o",
            tokens_used=200,
            processing_time=1.2
        )
        yield mock

@pytest.fixture
def mock_memory_manager():
    with patch('app.api.v1.endpoints.risk.MemoryManager') as mock:
        yield mock

def test_assess_risk_success(mock_llm_orchestrator, mock_memory_manager):
    """Test successful risk assessment request."""
    test_data = {
        "customer_id": "cust_123",
        "transaction_history": [
            {
                "id": "txn_1",
                "amount": 100.0,
                "date": "2023-01-01",
                "category": "groceries",
                "type": "debit"
            },
            {
                "id": "txn_2",
                "amount": 2000.0,
                "date": "2023-01-02",
                "category": "income",
                "type": "credit"
            }
        ],
        "account_balances": {
            "checking": 5000.0,
            "savings": 15000.0
        },
        "credit_score": 750,
        "income": 80000.0,
        "employment_status": "employed",
        "risk_preference": "moderate",
        "time_horizon": "5y"
    }
    
    response = client.post("/api/v1/risk/assess", json=test_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_123"
    assert 0 <= data["overall_risk_score"] <= 1
    assert data["risk_level"] in ["very_low", "low", "moderate", "high", "very_high"]
    assert len(data["risk_factors"]) > 0
    assert len(data["recommendations"]) > 0

def test_get_risk_score():
    """Test retrieval of risk score for a customer."""
    customer_id = "cust_123"
    response = client.get(f"/api/v1/risk/score/{customer_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == customer_id
    assert 0 <= data["risk_score"] <= 1
    assert data["risk_level"] in ["very_low", "low", "moderate", "high", "very_high"]
    assert "last_updated" in data

def test_assess_risk_invalid_data():
    """Test risk assessment with invalid data."""
    invalid_data = {
        "customer_id": "cust_123",
        "transaction_history": [
            {
                "id": "txn_1",
                "amount": "not_a_number",  # Invalid type
                "date": "2023-01-01",
                "category": "groceries",
                "type": "invalid_type"  # Invalid enum value
            }
        ],
        "account_balances": {}
    }
    
    response = client.post("/api/v1/risk/assess", json=invalid_data)
    assert response.status_code == 422  # Validation error

def test_assess_risk_empty_transactions():
    """Test risk assessment with empty transaction history."""
    test_data = {
        "customer_id": "cust_123",
        "transaction_history": [],
        "account_balances": {
            "checking": 1000.0,
            "savings": 5000.0
        }
    }
    
    response = client.post("/api/v1/risk/assess", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_123"
    assert len(data["risk_factors"]) > 0
