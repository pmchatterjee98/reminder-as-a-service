"""
Security utilities for RAAS - Encryption, decryption, and secure data handling.
Implements field-level encryption for sensitive user contact information.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional

class EncryptionManager:
    """Manages encryption and decryption of sensitive user data."""
    
    def __init__(self):
        """Initialize encryption manager with Fernet cipher."""
        self.cipher = self._get_cipher()
    
    def _get_cipher(self) -> Fernet:
        """
        Get or create Fernet cipher using encryption key from environment.
        Falls back to generating a new key if none exists (dev/testing only).
        """
        encryption_key = os.getenv('ENCRYPTION_KEY')
        
        if not encryption_key:
            # Development fallback: generate deterministic key
            # In production, this MUST be set in Replit Secrets
            password = os.getenv('SESSION_SECRET', 'raas-dev-key-change-in-production')
            salt = b'raas_salt_v1'
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return Fernet(key)
        
        return Fernet(encryption_key.encode())
    
    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt (e.g., email, phone number)
        
        Returns:
            Base64-encoded encrypted string, or None if input is None/empty
        """
        if not plaintext:
            return None
        
        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode())
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            raise
    
    def decrypt(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: Encrypted string to decrypt
        
        Returns:
            Decrypted plaintext string, or None if input is None/empty
        """
        if not ciphertext:
            return None
        
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            raise
    
    def encrypt_contact_info(self, email: Optional[str] = None, 
                            phone: Optional[str] = None,
                            whatsapp: Optional[str] = None) -> dict:
        """
        Encrypt contact information fields.
        
        Args:
            email: Email address
            phone: Phone number
            whatsapp: WhatsApp number
        
        Returns:
            Dictionary with encrypted values (None values preserved)
        """
        return {
            'email_encrypted': self.encrypt(email),
            'phone_encrypted': self.encrypt(phone),
            'whatsapp_encrypted': self.encrypt(whatsapp)
        }
    
    def decrypt_contact_info(self, email_encrypted: Optional[str] = None,
                            phone_encrypted: Optional[str] = None,
                            whatsapp_encrypted: Optional[str] = None) -> dict:
        """
        Decrypt contact information fields.
        
        Args:
            email_encrypted: Encrypted email
            phone_encrypted: Encrypted phone
            whatsapp_encrypted: Encrypted WhatsApp
        
        Returns:
            Dictionary with decrypted plaintext values
        """
        return {
            'email': self.decrypt(email_encrypted),
            'phone': self.decrypt(phone_encrypted),
            'whatsapp': self.decrypt(whatsapp_encrypted)
        }


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if email format appears valid
    """
    if not email or '@' not in email:
        return False
    
    parts = email.split('@')
    return len(parts) == 2 and len(parts[0]) > 0 and '.' in parts[1]


def validate_phone(phone: str) -> bool:
    """
    Basic phone number validation (supports international format).
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if phone format appears valid
    """
    if not phone:
        return False
    
    # Remove common formatting characters
    cleaned = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    
    # Check if remaining characters are digits and length is reasonable
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate to max length
    sanitized = text[:max_length]
    
    # Remove any null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    return sanitized.strip()


def hash_email(email: str) -> str:
    """
    Hash an email address for secure lookups and uniqueness constraints.
    Uses SHA-256 hashing to create a deterministic hash that can be indexed.
    
    Args:
        email: Email address to hash (case-insensitive)
    
    Returns:
        Hex-encoded SHA-256 hash of the email
    """
    # Normalize email to lowercase for consistent hashing
    normalized_email = email.lower().strip()
    
    # SHA-256 hash
    return hashlib.sha256(normalized_email.encode()).hexdigest()
