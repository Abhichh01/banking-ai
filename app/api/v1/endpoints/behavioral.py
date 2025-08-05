"""
Behavioral Analysis Endpoint

This module provides endpoints for analyzing customer behavior patterns.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.llm_orchestrator import LLMOrchestrator, TaskType, TaskComplexity, LLMResponse
from app.core.memory_manager import MemoryManager
from app.api.v1.dependencies import get_current_active_user, get_async_db
from app.repositories.enhanced_behavioral_pattern import EnhancedBehavioralPatternRepository
from app.schemas.behavioral import (
    Transaction,
    BehavioralInsight,
    BehavioralAnalysisRequest,
    BehavioralAnalysisResponse
)
from app.schemas.user import UserInDB
from app.schemas.response import StandardResponse

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Setup for repositories
async def get_behavioral_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedBehavioralPatternRepository:
    """Dependency to get a behavioral pattern repository."""
    llm_orchestrator = LLMOrchestrator()
    memory_manager = MemoryManager()
    return EnhancedBehavioralPatternRepository(db, llm_orchestrator, memory_manager)

@router.post("/analyze", response_model=StandardResponse)
async def analyze_behavior(
    request: BehavioralAnalysisRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    behavioral_repo: EnhancedBehavioralPatternRepository = Depends(get_behavioral_repository)
):
    """
    Analyze customer transaction behavior.
    
    This endpoint analyzes a customer's transaction history to identify
    spending patterns, behavioral biases, and potential financial risks.
    """
    try:
        # Analyze behavior using the repository
        analysis_result = await behavioral_repo.analyze_user_behavior(
            user_id=current_user.id,
            transactions=request.transactions,
            time_period=request.time_period
        )
        
        return StandardResponse(
            success=True,
            message="Behavioral analysis completed successfully",
            data=analysis_result
        )
        
    except Exception as e:
        logger.error(f"Error processing behavioral analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing behavioral analysis: {str(e)}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing behavioral analysis: {str(e)}"
        )
