"""
Risk Assessment Endpoint

This module provides endpoints for assessing financial risk.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_orchestrator import LLMOrchestrator, TaskType, TaskComplexity
from app.core.memory_manager import MemoryManager
from app.api.v1.dependencies import get_current_active_user, get_async_db
from app.repositories.enhanced_fraud_alert import EnhancedFraudAlertRepository
from app.schemas.risk import (
    RiskLevel,
    RiskFactor,
    RiskAssessmentRequest,
    RiskAssessmentResponse
)
from app.schemas.user import UserInDB
from app.schemas.response import StandardResponse

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Setup for repositories
async def get_fraud_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedFraudAlertRepository:
    """Dependency to get a fraud alert repository."""
    llm_orchestrator = LLMOrchestrator()
    memory_manager = MemoryManager()
    return EnhancedFraudAlertRepository(db, llm_orchestrator, memory_manager)

@router.post("/assess", response_model=StandardResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    fraud_repo: EnhancedFraudAlertRepository = Depends(get_fraud_repository)
):
    """
    Perform a comprehensive risk assessment for a customer.
    
    This endpoint analyzes various risk factors including transaction patterns,
    account balances, credit history, and more to generate a risk profile.
    """
    try:
        # Perform risk assessment using the repository
        risk_assessment = await fraud_repo.assess_user_risk(
            user_id=current_user.id,
            transaction_history=request.transaction_history,
            account_balances=request.account_balances,
            credit_score=request.credit_score,
            income=request.income,
            employment_status=request.employment_status,
            existing_loans=request.existing_loans,
            investment_portfolio=request.investment_portfolio,
            risk_preference=request.risk_preference,
            time_horizon=request.time_horizon
        )
        
        return StandardResponse(
            success=True,
            message="Risk assessment completed successfully",
            data=risk_assessment
        )
        
    except Exception as e:
        logger.error(f"Error processing risk assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing risk assessment: {str(e)}"
        )

@router.get("/score/{user_id}", response_model=StandardResponse)
async def get_risk_score(
    user_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    fraud_repo: EnhancedFraudAlertRepository = Depends(get_fraud_repository)
):
    """
    Get the latest risk score for a customer.
    
    This endpoint retrieves the most recent risk assessment for a customer
    or performs a new assessment if none exists.
    """
    try:
        # Check if the user is authorized to view this risk score
        if not current_user.is_superuser and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user's risk score"
            )
        
        # Get the risk score from the repository
        risk_score = await fraud_repo.get_user_risk_score(int(user_id))
        
        return StandardResponse(
            success=True,
            message=f"Retrieved risk score for user {user_id}",
            data=risk_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving risk score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving risk score: {str(e)}"
        )
