"""
Replit JWT Token Validation

Provides cryptographic verification of Replit Auth tokens using JWKS.
This ensures that user identity cannot be spoofed via header manipulation.
"""

import jwt
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading

# JWKS caching
_jwks_cache = None
_jwks_cache_time = None
_jwks_lock = threading.Lock()
JWKS_CACHE_DURATION = timedelta(hours=24)  # Cache JWKS for 24 hours


class ReplitJWTError(Exception):
    """Base exception for Replit JWT validation errors"""
    pass


class TokenExpiredError(ReplitJWTError):
    """Token has expired"""
    pass


class TokenInvalidError(ReplitJWTError):
    """Token is invalid or malformed"""
    pass


class JWKSFetchError(ReplitJWTError):
    """Failed to fetch JWKS from Replit"""
    pass


def get_jwks(force_refresh: bool = False) -> Dict:
    """
    Fetch JWKS (JSON Web Key Set) from Replit with caching.
    
    Attempts multiple known Replit JWKS endpoints in order of likelihood.
    Caches the result for 24 hours to avoid unnecessary network calls.
    
    Args:
        force_refresh: If True, bypass cache and fetch fresh JWKS
        
    Returns:
        Dict containing JWKS data
        
    Raises:
        JWKSFetchError: If JWKS cannot be fetched from any endpoint
    """
    global _jwks_cache, _jwks_cache_time
    
    # Check cache
    if not force_refresh and _jwks_cache and _jwks_cache_time:
        if datetime.now() - _jwks_cache_time < JWKS_CACHE_DURATION:
            return _jwks_cache
    
    # Known Replit JWKS endpoint candidates
    jwks_urls = [
        "https://replit.com/.well-known/jwks.json",
        "https://auth.replit.com/.well-known/jwks.json",
        "https://replit.com/.well-known/openid-configuration",  # Try OpenID config first
    ]
    
    with _jwks_lock:
        for url in jwks_urls:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # If we got OpenID config, extract jwks_uri
                if 'jwks_uri' in data:
                    jwks_response = requests.get(data['jwks_uri'], timeout=10)
                    jwks_response.raise_for_status()
                    _jwks_cache = jwks_response.json()
                else:
                    _jwks_cache = data
                
                _jwks_cache_time = datetime.now()
                return _jwks_cache
                
            except (requests.RequestException, ValueError) as e:
                # Try next URL
                continue
        
        # All URLs failed
        raise JWKSFetchError(
            "Could not fetch JWKS from any known Replit endpoint. "
            "This may indicate a network issue or Replit API change."
        )


def get_public_key_from_token(token: str) -> str:
    """
    Extract the public key from JWKS that matches the token's kid (key ID).
    
    Args:
        token: JWT token string
        
    Returns:
        Public key in PEM format
        
    Raises:
        TokenInvalidError: If token header is malformed or kid not found in JWKS
    """
    try:
        # Decode header without verification to get kid
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        
        if not kid:
            raise TokenInvalidError("Token missing 'kid' (key ID) in header")
        
        # Fetch JWKS
        jwks = get_jwks()
        
        # Find matching key
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                # Convert JWK to PEM format
                from jwt.algorithms import RSAAlgorithm
                public_key = RSAAlgorithm.from_jwk(key)
                return public_key
        
        raise TokenInvalidError(f"No public key found for kid '{kid}' in JWKS")
        
    except jwt.DecodeError as e:
        raise TokenInvalidError(f"Malformed token header: {str(e)}")


def verify_replit_token(token: str, expected_user_id: Optional[str] = None) -> Dict:
    """
    Verify and decode a Replit Auth JWT token.
    
    Performs full cryptographic verification:
    1. Fetches JWKS from Replit
    2. Validates signature using public key
    3. Checks expiration (exp claim)
    4. Checks issued-at time (iat claim)
    5. Verifies issuer (iss claim)
    6. Optionally verifies user ID matches (sub claim)
    
    Args:
        token: JWT token string
        expected_user_id: If provided, verify token's sub matches this user ID
        
    Returns:
        Dict containing decoded token claims (user_id in 'sub', etc.)
        
    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token signature is invalid or claims don't match
        JWKSFetchError: If JWKS cannot be fetched
    """
    try:
        # Get public key for this token
        public_key = get_public_key_from_token(token)
        
        # Decode and verify token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],  # Replit uses RS256
            issuer='https://replit.com',  # Verify issuer
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_iat': True,
                'verify_iss': True,
            }
        )
        
        # Optionally verify user ID
        if expected_user_id and decoded.get('sub') != expected_user_id:
            raise TokenInvalidError(
                f"Token user ID mismatch: expected '{expected_user_id}', "
                f"got '{decoded.get('sub')}'"
            )
        
        return decoded
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def extract_user_id_from_token(token: str) -> str:
    """
    Extract user ID from a verified Replit JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID (from 'sub' claim)
        
    Raises:
        TokenExpiredError, TokenInvalidError, JWKSFetchError
    """
    decoded = verify_replit_token(token)
    user_id = decoded.get('sub')
    
    if not user_id:
        raise TokenInvalidError("Token missing 'sub' (user ID) claim")
    
    return user_id
