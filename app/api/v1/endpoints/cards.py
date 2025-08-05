"""
Card API Endpoints

This module contains all API endpoints related to card management.
"""
from typing import List, Optional
from datetime import datetime, date
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_current_active_superuser, get_async_db
from app.schemas.account import Card, CardCreate, CardUpdate, CardInDB, CardStatus, CardType
from app.schemas.response import StandardResponse
from app.schemas.user import UserInDB
from app.models.card import Card as CardModel
from app.repositories.enhanced_card import EnhancedCardRepository
from app.repositories.enhanced_account import EnhancedAccountRepository
from app.core.llm_orchestrator import LLMOrchestrator

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize LLM Orchestrator
llm_orchestrator = LLMOrchestrator()

# Repository dependencies
async def get_card_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedCardRepository:
    """Dependency to get a card repository."""
    return EnhancedCardRepository(db, llm_orchestrator)

async def get_account_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedAccountRepository:
    """Dependency to get an account repository."""
    return EnhancedAccountRepository(db, llm_orchestrator)

@router.post("/", response_model=Card, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_in: CardCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository),
    account_repo: EnhancedAccountRepository = Depends(get_account_repository)
):
    """
    Request a new card
    """
    try:
        # Verify the account exists and belongs to the user
        if card_in.account_id:
            account = await account_repo.get_by_id(card_in.account_id)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account not found"
                )
            
            if account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to create a card for this account"
                )
        
        # Create the card
        card_data = card_in.dict()
        card_data["user_id"] = current_user.id
        
        # Create new card using repository
        card = await card_repo.create(card_data)
        await card_repo.db_session.commit()
        
        # Return the created card with masked sensitive data
        return card
        
    except HTTPException:
        raise
    except Exception as e:
        await card_repo.db_session.rollback()
        logger.error(f"Error creating card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating card: {str(e)}"
        )

@router.get("/", response_model=List[Card])
async def read_cards(
    skip: int = 0,
    limit: int = 50,
    status: Optional[CardStatus] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Retrieve cards for current user with optional status filter
    """
    try:
        # Get cards for the current user
        cards = await card_repo.get_cards_by_user(
            user_id=current_user.id,
            include_inactive=True if status is None else False,
            status=status
        )
        
        # Apply pagination
        paginated_cards = cards[skip: skip + limit]
        
        return paginated_cards
        
    except Exception as e:
        logger.error(f"Error retrieving cards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cards: {str(e)}"
        )

@router.get("/{card_id}", response_model=Card)
async def read_card(
    card_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Get a specific card by ID
    """
    try:
        # Get the card
        card = await card_repo.get_by_id(card_id)
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Only allow card owner or admin to view card
        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        return card
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving card: {str(e)}"
        )

@router.put("/{card_id}", response_model=Card)
async def update_card(
    card_id: int,
    card_in: CardUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Update card details
    """
    try:
        # Get the card
        card = await card_repo.get_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Only allow card owner or admin to update card
        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Update card data
        update_data = card_in.dict(exclude_unset=True)
        
        # Handle status changes (e.g., block/unblock)
        if 'status' in update_data:
            # In a real app, add validation for status transitions
            # For example: check if a card can be unblocked based on policy
            pass
        
        # Update the card using repository
        updated_card = await card_repo.update(card, update_data)
        await card_repo.db_session.commit()
        
        return updated_card
        
    except HTTPException:
        raise
    except Exception as e:
        await card_repo.db_session.rollback()
        logger.error(f"Error updating card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating card: {str(e)}"
        )

@router.post("/{card_id}/block", response_model=StandardResponse)
async def block_card(
    card_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Block a card
    """
    try:
        # Get the card
        card = await card_repo.get_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Only allow card owner or admin to block card
        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Update card status to blocked
        update_data = {"status": CardStatus.BLOCKED}
        await card_repo.update(card, update_data)
        await card_repo.db_session.commit()
        
        return StandardResponse(success=True, message="Card blocked successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await card_repo.db_session.rollback()
        logger.error(f"Error blocking card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error blocking card: {str(e)}"
        )

@router.post("/{card_id}/unblock", response_model=StandardResponse)
async def unblock_card(
    card_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Unblock a card
    """
    try:
        # Get the card
        card = await card_repo.get_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Only allow card owner or admin to unblock card
        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Update card status to active
        update_data = {"status": CardStatus.ACTIVE}
        await card_repo.update(card, update_data)
        await card_repo.db_session.commit()
        
        return StandardResponse(success=True, message="Card unblocked successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await card_repo.db_session.rollback()
        logger.error(f"Error unblocking card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unblocking card: {str(e)}"
        )

@router.delete("/{card_id}", response_model=StandardResponse)
async def delete_card(
    card_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Cancel a card (Admin only)
    """
    try:
        # Check if user is admin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # Get the card
        card = await card_repo.get_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Delete the card
        await card_repo.delete(card_id)
        await card_repo.db_session.commit()
        
        return StandardResponse(success=True, message="Card cancelled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        await card_repo.db_session.rollback()
        logger.error(f"Error cancelling card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling card: {str(e)}"
        )

@router.get("/{card_id}/transactions", response_model=List[dict])
async def get_card_transactions(
    card_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    card_repo: EnhancedCardRepository = Depends(get_card_repository)
):
    """
    Get transactions for a specific card
    """
    try:
        # Get the card
        card = await card_repo.get_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        # Only allow card owner or admin to view transactions
        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get the card transactions using repository
        transactions = await card_repo.get_card_transactions(
            card_id=card_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return transactions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving card transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving card transactions: {str(e)}"
        )
