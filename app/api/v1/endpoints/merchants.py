"""
Merchant API Endpoints

This module contains all API endpoints related to merchant management.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import UUID4

from app.api.v1.dependencies import (
    get_current_active_user, 
    get_current_active_superuser,
    get_async_db,
    PaginationParams,
    SortingParams
)
from app.schemas.merchant import (
    Merchant,
    MerchantCreate,
    MerchantUpdate,
    MerchantInDB,
    MerchantCategory,
    MerchantStatus,
    MerchantCategoryStats,
    MerchantSearchFilter,
    MerchantResponse,
    MerchantListResponse
)
from app.schemas.response import StandardResponse
from app.schemas.user import UserInDB
from app.repositories.enhanced_merchant import EnhancedMerchantRepository
from app.core.llm_orchestrator import LLMOrchestrator

# Create logger
logger = logging.getLogger(__name__)

# Create router with tags for better OpenAPI documentation
router = APIRouter(prefix="/merchants", tags=["Merchants"])

# Initialize LLM Orchestrator
llm_orchestrator = LLMOrchestrator()

# Repository dependencies
async def get_merchant_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedMerchantRepository:
    """Dependency to get a merchant repository."""
    return EnhancedMerchantRepository(db, llm_orchestrator)

@router.post(
    "", 
    response_model=MerchantResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new merchant",
    description="Create a new merchant account. Requires admin privileges.",
    response_description="The created merchant"
)
async def create_merchant(
    merchant_in: MerchantCreate,
    current_user: UserInDB = Depends(get_current_active_superuser),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> MerchantResponse:
    """
    Create a new merchant account.
    
    - **merchant_in**: Merchant data to create
    - **returns**: Created merchant with system-generated fields
    """
    try:
        # In a real app, validate merchant data against business rules
        
        # Create merchant data with user info
        merchant_data = merchant_in.dict()
        merchant_data["created_by"] = current_user.id
        merchant_data["updated_by"] = current_user.id
        merchant_data["status"] = MerchantStatus.ACTIVE
        
        # Create merchant in database
        merchant = await merchant_repo.create(merchant_data)
        await merchant_repo.db_session.commit()
        
        return MerchantResponse(
            success=True,
            message="Merchant created successfully",
            data=merchant
        )
    
    except Exception as e:
        await merchant_repo.db_session.rollback()
        logger.error(f"Error creating merchant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating merchant: {str(e)}"
        )

@router.get(
    "", 
    response_model=MerchantListResponse,
    summary="List merchants",
    description="Retrieve a paginated list of merchants with optional filtering and sorting.",
    response_description="Paginated list of merchants"
)
async def read_merchants(
    pagination: PaginationParams = Depends(),
    sorting: SortingParams = Depends(),
    name: Optional[str] = Query(
        None, 
        description="Filter by merchant name (case-insensitive, partial match)"
    ),
    category: Optional[MerchantCategory] = Query(
        None, 
        description="Filter by merchant category"
    ),
    status: Optional[MerchantStatus] = Query(
        None, 
        description="Filter by merchant status"
    ),
    current_user: UserInDB = Depends(get_current_active_user),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> MerchantListResponse:
    """
    Retrieve merchants with filtering, sorting, and pagination.
    
    - **name**: Filter by merchant name
    - **category**: Filter by merchant category
    - **status**: Filter by merchant status
    - **pagination**: Controls pagination (skip/limit)
    - **sorting**: Controls sorting (field and order)
    - **returns**: Paginated list of merchants
    """
    try:
        # Create a filter dictionary from the query parameters
        filters = {
            "name": name,
            "category": category,
            "status": status
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Get merchants from repository with filters
        merchants = await merchant_repo.search(
            filters=filters,
            skip=pagination.skip,
            limit=pagination.limit,
            sort_by=sorting.sort_by,
            sort_order=sorting.sort_order
        )
        
        # Get total count for pagination
        total_count = await merchant_repo.count(filters=filters)
        
        return MerchantListResponse(
            success=True,
            message="Merchants retrieved successfully",
            data=merchants,
            total=total_count,
            page=pagination.skip // pagination.limit + 1 if pagination.limit > 0 else 1,
            size=pagination.limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving merchants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving merchants: {str(e)}"
        )

@router.get(
    "/{merchant_id}", 
    response_model=MerchantResponse,
    summary="Get merchant by ID",
    description="Retrieve detailed information about a specific merchant.",
    responses={
        404: {"description": "Merchant not found"}
    }
)
async def read_merchant(
    merchant_id: str = Path(..., description="The ID of the merchant to retrieve"),
    current_user: UserInDB = Depends(get_current_active_user),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> MerchantResponse:
    """
    Get detailed information about a specific merchant.
    
    - **merchant_id**: The ID of the merchant to retrieve
    - **returns**: The requested merchant
    """
    try:
        merchant = await merchant_repo.get_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "merchant_not_found",
                    "message": f"Merchant with ID {merchant_id} not found"
                }
            )
        
        return MerchantResponse(
            success=True,
            message="Merchant retrieved successfully",
            data=merchant
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving merchant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving merchant: {str(e)}"
        )

@router.put(
    "/{merchant_id}", 
    response_model=MerchantResponse,
    summary="Update a merchant",
    description="Update an existing merchant's information. Requires admin privileges.",
    responses={
        404: {"description": "Merchant not found"}
    }
)
async def update_merchant(
    merchant_id: str,
    merchant_in: MerchantUpdate,
    current_user: UserInDB = Depends(get_current_active_superuser),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> MerchantResponse:
    """
    Update a merchant's information.
    
    - **merchant_id**: The ID of the merchant to update
    - **merchant_in**: The updated merchant data
    - **returns**: The updated merchant
    """
    try:
        # Get the merchant
        merchant = await merchant_repo.get_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "merchant_not_found",
                    "message": f"Merchant with ID {merchant_id} not found"
                }
            )
        
        # Update merchant data (excluding unset fields)
        update_data = merchant_in.dict(exclude_unset=True)
        
        # Add audit fields
        update_data["updated_by"] = current_user.id
        
        # Update the merchant
        updated_merchant = await merchant_repo.update(merchant, update_data)
        await merchant_repo.db_session.commit()
        
        return MerchantResponse(
            success=True,
            message="Merchant updated successfully",
            data=updated_merchant
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await merchant_repo.db_session.rollback()
        logger.error(f"Error updating merchant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating merchant: {str(e)}"
        )

@router.delete(
    "/{merchant_id}", 
    response_model=StandardResponse,
    summary="Delete a merchant",
    description="Delete a merchant by ID. Requires admin privileges.",
    responses={
        404: {"description": "Merchant not found"},
        400: {"description": "Cannot delete merchant with active transactions"}
    }
)
async def delete_merchant(
    merchant_id: str,
    current_user: UserInDB = Depends(get_current_active_superuser),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> StandardResponse:
    """
    Delete a merchant by ID.
    
    - **merchant_id**: The ID of the merchant to delete
    - **returns**: Success message
    """
    try:
        # Get the merchant
        merchant = await merchant_repo.get_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "merchant_not_found",
                    "message": f"Merchant with ID {merchant_id} not found"
                }
            )
        
        # Check for existing transactions
        has_transactions = await merchant_repo.has_transactions(merchant_id)
        if has_transactions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "merchant_has_transactions",
                    "message": "Cannot delete merchant with existing transactions"
                }
            )
        
        # Delete the merchant
        await merchant_repo.delete(merchant_id)
        await merchant_repo.db_session.commit()
        
        return StandardResponse(
            success=True,
            message="Merchant deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        await merchant_repo.db_session.rollback()
        logger.error(f"Error deleting merchant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting merchant: {str(e)}"
        )

@router.get(
    "/{merchant_id}/transactions",
    response_model=StandardResponse,
    summary="Get merchant transactions",
    description="Retrieve transactions for a specific merchant.",
    responses={
        404: {"description": "Merchant not found"}
    }
)
async def get_merchant_transactions(
    merchant_id: str,
    pagination: PaginationParams = Depends(),
    current_user: UserInDB = Depends(get_current_active_user),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> StandardResponse:
    """
    Get transactions for a specific merchant.
    
    - **merchant_id**: The ID of the merchant
    - **pagination**: Controls pagination (skip/limit)
    - **returns**: Paginated list of transactions
    """
    try:
        # Verify merchant exists
        merchant = await merchant_repo.get_by_id(merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "merchant_not_found",
                    "message": f"Merchant with ID {merchant_id} not found"
                }
            )
        
        # Get transactions for this merchant
        transactions = await merchant_repo.get_merchant_transactions(
            merchant_id=merchant_id,
            skip=pagination.skip,
            limit=pagination.limit
        )
        
        # Get total count for pagination
        total_count = await merchant_repo.count_merchant_transactions(merchant_id)
        
        return StandardResponse(
            success=True,
            message=f"Found {total_count} transactions for merchant {merchant_id}",
            data={
                "items": transactions,
                "total": total_count,
                "page": pagination.skip // pagination.limit + 1 if pagination.limit > 0 else 1,
                "size": pagination.limit
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving merchant transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving merchant transactions: {str(e)}"
        )

@router.get(
    "/categories/popular",
    response_model=StandardResponse,
    summary="Get popular merchant categories",
    description="Retrieve statistics about the most popular merchant categories.",
    response_description="List of categories with transaction statistics"
)
async def get_popular_categories(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of categories to return"),
    current_user: UserInDB = Depends(get_current_active_user),
    merchant_repo: EnhancedMerchantRepository = Depends(get_merchant_repository)
) -> StandardResponse:
    """
    Get most popular merchant categories by transaction volume and count.
    
    - **limit**: Maximum number of categories to return (1-100)
    - **returns**: List of categories with transaction statistics
    """
    try:
        # Fetch popular categories using the repository
        popular_categories = await merchant_repo.get_popular_categories(limit=limit)
        
        return StandardResponse(
            success=True,
            message=f"Retrieved top {len(popular_categories)} popular merchant categories",
            data={
                "items": popular_categories,
                "total": len(popular_categories)
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving popular merchant categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving popular merchant categories: {str(e)}"
        )
