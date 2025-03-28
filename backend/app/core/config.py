"""
Security module for NigeriaJustice.AI

Handles authentication, authorization, JWT token management, and 
security-related utilities.
"""

import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import ValidationError
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# API Key handling
api_key_header = APIKeyHeader(name="X-API-Key")

def get_password_hash(password: str) -> str:
    """
    Hash a password for storing
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT token
    """
    to_encode = data.copy()
    
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> Dict:
    """
    Decode a JWT token
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Get the current authenticated user from the token
    """
    try:
        payload = decode_token(token)
        
        # In production, this would verify user still exists in database
        # For now, just return the payload data
        return payload
    except (jwt.PyJWTError, ValidationError) as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Verify that the provided API key is valid
    """
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:5]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return True

def verify_court_role(allowed_roles: List[str]):
    """
    Factory function for creating role verification dependencies
    
    Usage:
    @router.get("/admin-only", dependencies=[Depends(verify_court_role(["admin"]))])
    async def admin_only():
        ...
    """
    async def _verify_court_role(current_user: Dict = Depends(get_current_user)) -> bool:
        user_role = current_user.get("role", "").lower()
        
        # Admin role has access to everything
        if user_role == "admin":
            return True
            
        if user_role not in [role.lower() for role in allowed_roles]:
            logger.warning(
                f"Unauthorized role access attempt: User with role '{user_role}' "
                f"tried to access resource requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}",
            )
        return True
    
    return _verify_court_role

def has_permission(permission: str):
    """
    Factory function for creating permission verification dependencies
    
    Usage:
    @router.post("/warrants", dependencies=[Depends(has_permission("issue_warrants"))])
    async def create_warrant():
        ...
    """
    async def _has_permission(current_user: Dict = Depends(get_current_user)) -> bool:
        user_role = current_user.get("role", "").lower()
        
        # Admin role has all permissions
        if user_role == "admin":
            return True
        
        # In production, this would look up the role's permissions in the database
        # For now, check against the court configuration
        roles = settings.COURT_CONFIG.get("roles", [])
        role_config = next((r for r in roles if r["id"] == user_role), None)
        
        if not role_config:
            logger.warning(f"Unknown role: {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Unknown role.",
            )
        
        role_permissions = role_config.get("permissions", [])
        
        # "view_all" and "edit_all" are special permissions that include all others
        if "view_all" in role_permissions and permission.startswith("view_"):
            return True
            
        if "edit_all" in role_permissions and permission.startswith("edit_"):
            return True
        
        if permission not in role_permissions:
            logger.warning(
                f"Unauthorized permission access attempt: User with role '{user_role}' "
                f"tried to use permission '{permission}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}",
            )
            
        return True
    
    return _has_permission

def anonymize_entity_object(entity_object: Dict, fields_to_anonymize: List[str]) -> Dict:
    """
    Anonymize sensitive fields in an object
    
    Args:
        entity_object: Dictionary containing entity data
        fields_to_anonymize: List of field names to anonymize
        
    Returns:
        Dictionary with anonymized fields
    """
    anonymized = entity_object.copy()
    
    for field in fields_to_anonymize:
        if field in anonymized:
            anonymized[field] = "[REDACTED]"
    
    return anonymized

def is_admin(current_user: Dict = Depends(get_current_user)) -> bool:
    """
    Check if the current user is an admin
    """
    if current_user.get("role", "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return True
