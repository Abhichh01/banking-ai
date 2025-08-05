"""
API Dependencies, Authentication, and Request Validation Utilities
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Type, TypeVar, Generic, List, Callable, AsyncGenerator

from fastapi import Depends, HTTPException, status, Query, Request, Body, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from jose.exceptions import JWTError as JoseError
from passlib.context import CryptContext
from pydantic import ValidationError, BaseModel, Field, validator
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.core.config import get_settings
from app.db.database import Database
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.schemas.token import TokenData
from app.schemas.user import UserInDB
from app.schemas.response import ErrorResponse, ValidationErrorResponse

# Generic Type Variables
T = TypeVar('T')

class PaginationParams:
    """Dependency for pagination parameters"""
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    ):
        self.skip = skip
        self.limit = limit

class SortingParams:
    """Dependency for sorting parameters"""
    def __init__(
        self,
        sort_by: str = Query("created_at", description="Field to sort by"),
        sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order (asc/desc)")
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order

settings = get_settings()

# Database dependency
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    
    Yields:
        AsyncSession: An async SQLAlchemy session
        
    Example:
        async def some_endpoint(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(User))
    """
    db = Database()
    async with db.session_scope() as session:
        yield session
        await session.close()

# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

# Rate limiting store (in-memory for demo, use Redis in production)
rate_limit_store = {}
rate_limit_window = 60  # seconds
rate_limit_max = 100  # requests per window

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_token_from_header(authorization: str = Depends(oauth2_scheme)) -> str:
    """Extract token from Authorization header"""
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return authorization.split(" ")[1]

async def rate_limit_check(request: Request) -> None:
    """Check and enforce rate limiting"""
    client_ip = request.client.host
    current_time = int(datetime.utcnow().timestamp())
    window_start = current_time - rate_limit_window
    
    # Clean up old entries
    rate_limit_store[client_ip] = [t for t in rate_limit_store.get(client_ip, []) 
                                 if t > window_start]
    
    # Check rate limit
    if len(rate_limit_store.get(client_ip, [])) >= rate_limit_max:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(rate_limit_window)}
        )
    
    # Update rate limit store
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    rate_limit_store[client_ip].append(current_time)

async def get_current_user(token: str = Depends(get_token_from_header)) -> UserInDB:
    """Get current authenticated user from JWT token with enhanced validation"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "invalid_credentials",
            "message": "Could not validate credentials"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}
        )
        
        # Validate required claims
        required_claims = {"sub", "exp", "iat"}
        if not all(claim in payload for claim in required_claims):
            raise credentials_exception
            
        # Check expiration
        current_time = datetime.utcnow().timestamp()
        if payload["exp"] < current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "token_expired",
                    "message": "Token has expired"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Validate token type if present
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "invalid_token_type",
                    "message": "Refresh tokens cannot be used for authentication"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
            
        token_data = TokenData(username=username)
        
        # In a real app, fetch user from database
        # user = await user_repo.get_by_username(username=token_data.username)
        # if not user:
        #     raise credentials_exception
        # return user
        
        # Mock user for development
        return UserInDB(
            id=1,
            username=token_data.username,
            email=f"{token_data.username}@example.com",
            full_name="Test User",
            hashed_password="",
            is_active=True,
            is_superuser=False,
            permissions=["read:profile", "write:profile", "read:transactions"]
        )
        
    except (JWTError, JoseError, ValidationError) as e:
        error_detail = str(e)
        if isinstance(e, JWTError):
            error_detail = "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "token_validation_failed",
                "message": error_detail
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """
    Get current active user.
    
    Args:
        current_user: The authenticated user from the JWT token.
        
    Returns:
        The active user if found and active.
        
    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "inactive_user",
                "message": "This user account has been deactivated"
            }
        )
    return current_user

def get_current_active_superuser(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """
    Get current active superuser.
    
    Args:
        current_user: The authenticated user from the JWT token.
        
    Returns:
        The user if they are a superuser.
        
    Raises:
        HTTPException: If the user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "insufficient_permissions",
                "message": "The user doesn't have enough privileges"
            }
        )
    return current_user

def check_permission(required_permission: str):
    """
    Dependency to check if user has a specific permission.
    
    Args:
        required_permission: The permission string to check (e.g., 'read:transactions')
        
    Returns:
        A dependency that checks for the specified permission.
    """
    def permission_checker(
        current_user: UserInDB = Depends(get_current_active_user)
    ) -> UserInDB:
        """Check if user has the required permission."""
        if (not current_user.is_superuser and 
            required_permission not in (current_user.permissions or [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "permission_denied",
                    "message": f"Missing required permission: {required_permission}"
                }
            )
        return current_user
    return permission_checker

# Custom exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent error format."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        error_detail = exc.detail
    else:
        error_detail = {
            "code": "request_error",
            "message": str(exc.detail) if exc.detail else "An error occurred"
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_detail}
    )

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors with consistent format."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field or "body",
            "code": error["type"],
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Validation failed",
                "details": errors
            }
        }
    )
