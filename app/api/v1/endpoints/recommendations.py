"""
Recommendations Endpoint with Behavior Analysis and Card Suggestions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.llm_orchestrator import LLMOrchestrator
from app.core.memory_manager import MemoryManager
from app.api.v1.dependencies import get_current_active_user, get_async_db
from app.repositories.enhanced_ai_recommendation import EnhancedAIRecommendationRepository
from app.repositories.enhanced_transaction import EnhancedTransactionRepository
from app.schemas.user import UserInDB
from app.schemas.response import StandardResponse
from app.models.ai_recommendation import RecommendationType

# Set up logger
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Setup for repositories
async def get_recommendation_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedAIRecommendationRepository:
    """Dependency to get an AI recommendation repository."""
    llm_orchestrator = LLMOrchestrator()
    memory_manager = MemoryManager()
    return EnhancedAIRecommendationRepository(db, llm_orchestrator, memory_manager)

async def get_transaction_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedTransactionRepository:
    """Dependency to get a transaction repository."""
    llm_orchestrator = LLMOrchestrator()
    memory_manager = MemoryManager()
    return EnhancedTransactionRepository(db, llm_orchestrator, memory_manager)

@router.post("/analyze_spending", response_model=StandardResponse)
async def analyze_user_spending(
    current_user: UserInDB = Depends(get_current_active_user),
    recommendation_repo: EnhancedAIRecommendationRepository = Depends(get_recommendation_repository),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """Analyze user spending patterns and provide insights."""
    try:
        # Get user's transactions from transaction repository
        user_transactions = await transaction_repo.get_user_transactions(
            user_id=current_user.id,
            filters=None,
            skip=0,
            limit=1000  # Get a significant number of transactions for analysis
        )
        
        # Generate spending analysis using AI recommendation repository
        spending_analysis = await recommendation_repo.analyze_spending_patterns(
            user_id=current_user.id,
            transactions=user_transactions[0]  # Extract the transaction list from the tuple
        )
        
        # Get card recommendations based on spending patterns
        card_recommendations = await recommendation_repo.get_card_recommendations(
            user_id=current_user.id,
            spending_analysis=spending_analysis
        )
        
        return StandardResponse(
            success=True,
            message="Spending analysis completed successfully",
            data={
                "spending_analysis": spending_analysis,
                "card_recommendations": card_recommendations
            }
        )
    except Exception as e:
        logger.error(f"Error analyzing spending: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing spending: {str(e)}"
        )

@router.post("/personalized", response_model=StandardResponse)
async def generate_personalized_recommendations(
    request_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
    recommendation_repo: EnhancedAIRecommendationRepository = Depends(get_recommendation_repository)
):
    """
    Generate personalized financial recommendations based on the user's profile,
    goals, risk tolerance, and transaction history.
    """
    try:
        # Extract relevant information from the request
        goals = request_data.get("goals", [])
        risk_tolerance = request_data.get("risk_tolerance", "moderate")
        time_horizon = request_data.get("time_horizon", "medium_term")
        
        # Generate personalized recommendations using the repository
        recommendations = await recommendation_repo.generate_personalized_recommendations(
            user_id=current_user.id,
            goals=goals,
            risk_tolerance=risk_tolerance,
            time_horizon=time_horizon
        )
        
        return StandardResponse(
            success=True,
            message="Personalized recommendations generated successfully",
            data=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating personalized recommendations: {str(e)}"
        )

@router.get("/products", response_model=StandardResponse)
async def get_recommended_products(
    product_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_amount: Optional[float] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    recommendation_repo: EnhancedAIRecommendationRepository = Depends(get_recommendation_repository)
):
    """
    Get recommended financial products based on customer profile.
    """
    try:
        # Get recommended products using the repository
        products = await recommendation_repo.get_recommended_products(
            user_id=current_user.id,
            product_type=product_type,
            risk_level=risk_level,
            min_amount=min_amount
        )
        
        return StandardResponse(
            success=True,
            message=f"Found {len(products)} recommended products",
            data=products
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recommended products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recommended products: {str(e)}"
        )
