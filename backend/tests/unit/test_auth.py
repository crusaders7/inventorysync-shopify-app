"""Unit tests for authentication"""

import pytest
from datetime import datetime, timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_jwt,
    create_refresh_token
)

@pytest.mark.unit
class TestPasswordHashing:
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

@pytest.mark.unit
class TestJWT:
    def test_create_access_token(self):
        """Test creating access token"""
        data = {"sub": "test_user", "scopes": ["read", "write"]}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_decode_jwt_valid(self):
        """Test decoding valid JWT"""
        data = {"sub": "test_user", "scopes": ["read", "write"]}
        token = create_access_token(data)
        
        decoded = decode_jwt(token)
        assert decoded is not None
        assert decoded["sub"] == "test_user"
        assert decoded["scopes"] == ["read", "write"]
    
    def test_decode_jwt_expired(self):
        """Test decoding expired JWT"""
        data = {"sub": "test_user"}
        # Create token with negative expiration
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        decoded = decode_jwt(token)
        assert decoded is None
    
    def test_decode_jwt_invalid(self):
        """Test decoding invalid JWT"""
        invalid_token = "invalid.jwt.token"
        
        decoded = decode_jwt(invalid_token)
        assert decoded is None
    
    def test_create_refresh_token(self):
        """Test creating refresh token"""
        data = {"sub": "test_user"}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        decoded = decode_jwt(token)
        assert decoded is not None
        assert decoded["type"] == "refresh"
