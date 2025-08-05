"""
Transaction API Endpoints

This module contains all API endpoints related to transaction management.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.v1.dependencies import get_current_active_user, get_current_active_superuser, get_async_db
from app.repositories.enhanced_transaction import EnhancedTransactionRepository
from app.schemas.transaction import (
    Transaction, 
    TransactionCreate, 
    TransactionUpdate, 
    TransactionType,
    TransactionStatus,
    TransactionCategory,
    TransactionFilter
)
from app.schemas.response import StandardResponse, PaginatedResponse
from app.schemas.user import UserInDB
from app.core.llm_orchestrator import LLMOrchestrator
from app.core.memory_manager import MemoryManager

# Create router
router = APIRouter()

# Setup for repositories
async def get_transaction_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedTransactionRepository:
    """Dependency to get a transaction repository."""
    llm_orchestrator = LLMOrchestrator()
    memory_manager = MemoryManager()
    return EnhancedTransactionRepository(db, llm_orchestrator, memory_manager)

class TransactionFilter(BaseModel):
    """Filter criteria for transactions"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    merchant_id: Optional[int] = None
    account_id: Optional[int] = None
    category: Optional[str] = None

@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_in: TransactionCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Create a new transaction
    """
    # Verify account ownership
    if not current_user.is_superuser:
        account = await transaction_repo.verify_account_ownership(
            transaction_in.account_id, 
            current_user.id
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create transactions for this account"
            )
    
    try:
        # Create the transaction using the repository
        new_transaction = await transaction_repo.create_transaction(
            transaction_in,
            perform_ai_analysis=True
        )
        
        return new_transaction
    except Exception as e:
        # Handle specific exceptions
        if hasattr(e, 'status_code'):
            raise HTTPException(
                status_code=e.status_code,
                detail=str(e)
            )
        # Generic error handling
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse[Transaction])
async def read_transactions(
    skip: int = 0,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    merchant_id: Optional[int] = None,
    account_id: Optional[int] = None,
    category: Optional[TransactionCategory] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Retrieve transactions with filtering and pagination
    """
    # Create filter for transactions
    filters = TransactionFilter(
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        transaction_type=transaction_type,
        status=status,
        merchant_id=merchant_id,
        account_id=account_id,
        category=category
    )
    
    # Get user's account IDs
    if not current_user.is_superuser and account_id is not None:
        # Verify the account belongs to the user
        account = await transaction_repo.verify_account_ownership(account_id, current_user.id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this account"
            )
    
    # Get transactions with filters
    try:
        if account_id:
            # Get transactions for specific account
            transactions, total = await transaction_repo.get_account_transactions(
                account_id=account_id,
                start_date=filters.start_date,
                end_date=filters.end_date,
                transaction_type=filters.transaction_type,
                status=filters.status,
                category=filters.category,
                min_amount=filters.min_amount,
                max_amount=filters.max_amount,
                skip=skip,
                limit=limit
            )
        else:
            # Get all user transactions across accounts
            transactions, total = await transaction_repo.get_user_transactions(
                user_id=current_user.id,
                filters=filters,
                skip=skip,
                limit=limit
            )
        
        return {
            "data": transactions,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}"
        )

@router.get("/{transaction_id}", response_model=Transaction)
async def read_transaction(
    transaction_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Get a specific transaction by ID
    """
    try:
        # Get the transaction from the database
        transaction = await transaction_repo.get(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check authorization - only owner or admin can view
        if not current_user.is_superuser:
            # Verify the transaction's account belongs to the user
            account = await transaction_repo.verify_account_ownership(
                transaction.account_id, 
                current_user.id
            )
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this transaction"
                )
        
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transaction: {str(e)}"
        )

@router.put("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    transaction_in: TransactionUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Update a transaction
    """
    try:
        # Get the existing transaction
        transaction = await transaction_repo.get(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Verify permissions
        if not current_user.is_superuser:
            # Verify the transaction's account belongs to the user
            account = await transaction_repo.verify_account_ownership(
                transaction.account_id, 
                current_user.id
            )
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this transaction"
                )
        
        # Update the transaction
        updated_transaction = await transaction_repo.update(
            id=transaction_id,
            obj_in=transaction_in
        )
        
        return updated_transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating transaction: {str(e)}"
        )

@router.delete("/{transaction_id}", response_model=StandardResponse)
async def delete_transaction(
    transaction_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Delete a transaction (Admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    try:
        # Get the transaction
        transaction = await transaction_repo.get(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Delete the transaction (soft delete)
        await transaction_repo.remove(transaction_id)
        
        return {"success": True, "message": "Transaction deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting transaction: {str(e)}"
        )

@router.get("/summary/categories", response_model=Dict[str, float])
async def get_category_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[int] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    transaction_repo: EnhancedTransactionRepository = Depends(get_transaction_repository)
):
    """
    Get spending summary by category
    """
    try:
        # If account_id provided, verify ownership
        if account_id and not current_user.is_superuser:
            account = await transaction_repo.verify_account_ownership(
                account_id, 
                current_user.id
            )
            
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this account"
                )
        
        # Get category summary from repository
        category_summary = await transaction_repo.get_category_summary(
            user_id=current_user.id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return category_summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving category summary: {str(e)}"
        )
