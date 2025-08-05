"""
Account API Endpoints with Analytics

This module contains all API endpoints related to account management and analytics.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Path
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, and_
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime, timedelta

from app.api.v1.dependencies import (
    get_current_active_user, 
    get_current_active_superuser,
    get_async_db
)
from app.models.account import Account as AccountModel
from app.models.transaction import Transaction, TransactionType
from app.repositories.enhanced_account import EnhancedAccountRepository
from app.repositories.enhanced_transaction import EnhancedTransactionRepository
from app.repositories.enhanced_ai_recommendation import EnhancedAIRecommendationRepository
from app.schemas.account import Account, AccountCreate, AccountUpdate, AccountInDB
from app.schemas.analytics import (
    BalanceHistoryResponse,
    SpendingByCategoryResponse,
    CashFlowResponse,
    AnalyticsTimeRange,
    AnalyticsTimeInterval
)
from app.schemas.response import StandardResponse, SuccessResponse
from app.schemas.user import UserInDB
from app.core.llm_orchestrator import LLMOrchestrator

# Create router
router = APIRouter(prefix="/accounts", tags=["accounts"])
analytics_router = APIRouter(prefix="/analytics/accounts", tags=["account-analytics"])

# Initialize LLM Orchestrator
llm_orchestrator = LLMOrchestrator()

# Repository dependencies
async def get_account_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedAccountRepository:
    """Dependency to get an account repository."""
    return EnhancedAccountRepository(db, llm_orchestrator)

async def get_transaction_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedTransactionRepository:
    """Dependency to get a transaction repository."""
    return EnhancedTransactionRepository(db, llm_orchestrator)

async def get_ai_recommendation_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedAIRecommendationRepository:
    """Dependency to get an AI recommendation repository."""
    return EnhancedAIRecommendationRepository(db, llm_orchestrator)

@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: AccountCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository)
):
    """
    Create a new account for the current user
    """
    try:
        # Check if user already has an account of this type
        existing_account = await account_repo.get_by_user_and_type(
            user_id=current_user.id,
            account_type=account_in.account_type
        )
        
        if existing_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a {account_in.account_type.value} account"
            )
            
        # Create new account
        account_data = account_in.dict()
        account_data["user_id"] = current_user.id
        
        account = await account_repo.create(account_data)
        await account_repo.db_session.commit()
        
        return account
        
    except HTTPException:
        raise
    except Exception as e:
        await account_repo.db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[Account])
async def read_accounts(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository)
):
    """
    Retrieve accounts for current user with pagination
    """
    try:
        accounts = await account_repo.get_user_accounts(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving accounts: {str(e)}"
        )

@router.get("/{account_id}", response_model=Account)
@cache(expire=300)  # Cache for 5 minutes
async def read_account(
    account_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository)
):
    """
    Get a specific account by ID with detailed information
    """
    try:
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Check permissions
        if account.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this account"
            )
        
        return account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving account: {str(e)}"
        )

@router.put("/{account_id}", response_model=Account)
async def update_account(
    account_id: int,
    account_in: AccountUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository)
):
    """
    Update account details
    """
    try:
        # Get the existing account
        account = await account_repo.get_by_id(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Check permissions
        if account.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this account"
            )
        
        # Update account data
        update_data = account_in.dict(exclude_unset=True)
        updated_account = await account_repo.update(account, update_data)
        await account_repo.db_session.commit()
        
        return updated_account
    
    except HTTPException:
        raise
    except Exception as e:
        await account_repo.db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating account: {str(e)}"
        )

@router.delete("/{account_id}", response_model=StandardResponse)
async def delete_account(
    account_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Delete or deactivate an account
    """
    # Get the account with transactions
    account = await account_repo.get_by_id(account_id, load_relationships=True)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check permissions
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this account"
        )
    
    try:
        # Check for pending transactions
        has_transactions = await transaction_repo.has_transactions(account_id)
        
        if has_transactions:
            # Soft delete (mark as inactive) if there are transactions
            await account_repo.update(account, {"is_active": False})
            message = "Account deactivated successfully (has transaction history)"
        else:
            # Hard delete if no transactions
            await account_repo.delete(account_id)
            message = "Account deleted successfully"
        
        await account_repo.db_session.commit()
        
        return StandardResponse(
            success=True,
            message=message
        )
        
    except Exception as e:
        await account_repo.db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}"
        )

@router.get("/{account_id}/balance", response_model=Dict[str, float])
@cache(expire=60)  # Cache for 1 minute
async def get_account_balance(
    account_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Get current balance and available balance of an account
    
    Returns:
        {
            "current_balance": float,
            "available_balance": float,
            "pending_transactions": float,
            "last_updated": datetime
        }
    """
    # Get the account
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check permissions
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this account"
        )
    
    try:
        # Get current balance from account
        current_balance = account.balance
        
        # Calculate available balance (current - pending transactions)
        pending_amount = await transaction_repo.get_pending_transactions_amount(account_id)
        available_balance = current_balance - pending_amount
        
        return {
            "current_balance": float(current_balance),
            "available_balance": float(available_balance),
            "pending_transactions": float(pending_amount),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating balance: {str(e)}"
        )

# ==================== Account Analytics Endpoints ====================

@analytics_router.get("/{account_id}/balance-history", response_model=BalanceHistoryResponse)
async def get_balance_history(
    account_id: int,
    time_range: AnalyticsTimeRange = Query(AnalyticsTimeRange.LAST_30_DAYS, description="Time range for the balance history"),
    interval: AnalyticsTimeInterval = Query(AnalyticsTimeInterval.DAILY, description="Time interval for data points"),
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository)
):
    """
    Get historical balance data for an account
    """
    # Get the account
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check permissions
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this account"
        )
    
    try:
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=time_range.value)
        
        # Get balance history from repository
        balance_history = await account_repo.get_balance_history(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            interval=interval.value
        )
        
        return BalanceHistoryResponse(
            account_id=account_id,
            time_range=time_range,
            interval=interval,
            data=balance_history
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving balance history: {str(e)}"
        )

@analytics_router.get("/{account_id}/spending-by-category", response_model=SpendingByCategoryResponse)
async def get_spending_by_category(
    account_id: int,
    time_range: AnalyticsTimeRange = Query(AnalyticsTimeRange.LAST_30_DAYS, description="Time range for the spending analysis"),
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Get spending analysis by category for an account
    """
    # Get the account
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check permissions
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this account"
        )
    
    try:
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=time_range.value)
        
        # Get spending by category from repository
        spending_data = await transaction_repo.get_spending_by_category(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return SpendingByCategoryResponse(
            account_id=account_id,
            time_range=time_range,
            data=spending_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving spending by category: {str(e)}"
        )

@analytics_router.get("/{account_id}/cash-flow", response_model=CashFlowResponse)
async def get_cash_flow_analysis(
    account_id: int,
    time_range: AnalyticsTimeRange = Query(AnalyticsTimeRange.LAST_90_DAYS, description="Time range for the cash flow analysis"),
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Get cash flow analysis for an account
    """
    # Get the account
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check permissions
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this account"
        )
    
    try:
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=time_range.value)
        
        # Get cash flow data from repository
        cash_flow_data = await transaction_repo.get_cash_flow_analysis(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return CashFlowResponse(
            account_id=account_id,
            time_range=time_range,
            data=cash_flow_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cash flow analysis: {str(e)}"
        )

@analytics_router.get("/{account_id}/ai-insights", response_model=Dict[str, Any])
async def get_ai_insights(
    account_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository),
    ai_repo: EnhancedAIRecommendationRepository = Depends(get_ai_recommendation_repository)
):
    """
    Get AI-powered insights and recommendations for an account
    """
    # Get the account
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check permissions
    if account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this account"
        )
    
    try:
        # Get AI insights from repository
        insights = await ai_repo.get_account_insights(
            account_id=account_id,
            user_id=current_user.id
        )
        
        return {
            "account_id": account_id,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI insights: {str(e)}"
        )
