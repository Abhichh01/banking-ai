"""
API v1 Router Configuration

This module defines the main API router and includes all endpoint routers.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_current_active_user,
    get_current_active_superuser,
    create_access_token,
    verify_password,
    get_async_db,
    rate_limit_check
)
from app.repositories.enhanced_user import EnhancedUserRepository
from app.schemas.user import UserCreate, UserInDB
from app.core.config import get_settings
from app.schemas.token import Token
from app.schemas.user import User, UserInDB, UserCreate, UserUpdate

# Import endpoint routers
from app.api.v1.endpoints import (
    health,
    behavioral,
    recommendations,
    risk,
    users,
    accounts,
    cards,
    transactions,
    merchants
)

settings = get_settings()

# Create main API router
api_router = APIRouter()

# Authentication endpoints
@api_router.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user_repo = EnhancedUserRepository(db)
    
    # Authenticate user
    user = await user_repo.authenticate(
        username=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login timestamp
    await user_repo.update_last_login(user.id)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/test-token", response_model=User, tags=["Authentication"])
async def test_token(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Test access token for current user
    """
    return current_user

# Include endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(cards.router, prefix="/cards", tags=["Cards"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["Merchants"])
api_router.include_router(behavioral.router, prefix="/behavioral", tags=["Behavioral Analysis"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Assessment"])

@api_router.post("/auth/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user account
    """
    # Rate limiting check
    await rate_limit_check(request)
    
    user_repo = EnhancedUserRepository(db)
    
    # Check if email already exists
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create new user
        user_dict = user_in.dict(exclude_unset=True)
        
        # Create user in database
        user = await user_repo.create(user_dict)
        
        # Generate verification token (optional: implement email verification)
        verification_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(hours=24)  # 24-hour expiration
        )
        
        # TODO: Uncomment and implement email sending when ready
        # if settings.EMAILS_ENABLED:
        #     background_tasks.add_task(
        #         send_verification_email,
        #         email=user.email,
        #         token=verification_token,
        #         username=user.first_name
        #     )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )
