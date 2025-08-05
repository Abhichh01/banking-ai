"""
User API Endpoints

This module contains all API endpoints related to user management.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_current_active_superuser, get_async_db
from app.repositories.enhanced_user import EnhancedUserRepository
from app.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.schemas.response import StandardResponse
from app.core.llm_orchestrator import LLMOrchestrator
from app.core.memory_manager import MemoryManager

# Create router
router = APIRouter()

# Setup for repositories
async def get_user_repository(
    db: AsyncSession = Depends(get_async_db),
) -> EnhancedUserRepository:
    """Dependency to get a user repository."""
    llm_orchestrator = LLMOrchestrator()
    memory_manager = MemoryManager()
    return EnhancedUserRepository(db, llm_orchestrator, memory_manager)

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: UserInDB = Depends(get_current_active_superuser),
    user_repo: EnhancedUserRepository = Depends(get_user_repository)
):
    """
    Create a new user (Admin only)
    """
    try:
        # Check if email already exists
        existing_user = await user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
            
        # Create new user
        user = await user_repo.create(user_in)
        
        # Commit the transaction
        await user_repo.db_session.commit()
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        await user_repo.db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_superuser),
    user_repo: EnhancedUserRepository = Depends(get_user_repository)
):
    """
    Retrieve users (Admin only)
    """
    try:
        users, _ = await user_repo.get_multi(skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get current user
    """
    return current_user

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    user_repo: EnhancedUserRepository = Depends(get_user_repository)
):
    """
    Get a specific user by ID
    """
    # Only allow superusers to access other users' data
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user = await user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    user_repo: EnhancedUserRepository = Depends(get_user_repository)
):
    """
    Update a user
    """
    # Only allow users to update their own data, unless they're superusers
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        # Get existing user
        user = await user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user
        updated_user = await user_repo.update(
            id=user_id,
            obj_in=user_in
        )
        
        # Commit the transaction
        await user_repo.db_session.commit()
        
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        await user_repo.db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.delete("/{user_id}", response_model=StandardResponse)
async def delete_user(
    user_id: int,
    current_user: UserInDB = Depends(get_current_active_superuser),
    user_repo: EnhancedUserRepository = Depends(get_user_repository)
):
    """
    Delete a user (Admin only)
    """
    try:
        # Get existing user
        user = await user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete the user (soft delete)
        await user_repo.remove(user_id)
        
        # Commit the transaction
        await user_repo.db_session.commit()
        
        return {"success": True, "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await user_repo.db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )
