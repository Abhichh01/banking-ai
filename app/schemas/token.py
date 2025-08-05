"""
Token-related Pydantic schemas for authentication.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema for access token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type, typically 'bearer'")
    expires_in: Optional[int] = Field(
        None, 
        description="Number of seconds until the token expires"
    )
    refresh_token: Optional[str] = Field(
        None,
        description="Refresh token that can be used to obtain a new access token"
    )


class TokenData(BaseModel):
    """Schema for token payload data."""
    sub: Optional[int] = Field(
        None, 
        description="Subject (user ID) of the token"
    )
    email: Optional[str] = Field(
        None,
        description="Email of the authenticated user"
    )
    exp: Optional[datetime] = Field(
        None,
        description="Expiration time of the token"
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="List of scopes/permissions granted to the token"
    )
    is_superuser: bool = Field(
        False,
        description="Whether the user has superuser privileges"
    )


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")


class TokenPair(BaseModel):
    """Schema for access and refresh token pair."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field("bearer", description="Token type, typically 'bearer'")
    expires_in: int = Field(..., description="Number of seconds until the access token expires")
