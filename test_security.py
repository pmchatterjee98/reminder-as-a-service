"""
Unit tests for security.py - Encryption and validation utilities.
"""

import pytest
import os
from security import (
    EncryptionManager,
    validate_email,
    validate_phone,
    sanitize_input,
    hash_email
)


class TestEncryptionManager:
    """Test cases for encryption and decryption."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        manager = EncryptionManager()
        plaintext = "test@example.com"
        
        encrypted = manager.encrypt(plaintext)
        assert encrypted is not None
        assert encrypted != plaintext
        
        decrypted = manager.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_none(self):
        """Test encrypting None returns None."""
        manager = EncryptionManager()
        assert manager.encrypt(None) is None
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string returns None."""
        manager = EncryptionManager()
        assert manager.encrypt("") is None
    
    def test_decrypt_none(self):
        """Test decrypting None returns None."""
        manager = EncryptionManager()
        assert manager.decrypt(None) is None
    
    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns None."""
        manager = EncryptionManager()
        assert manager.decrypt("") is None
    
    def test_encrypt_phone_number(self):
        """Test encrypting a phone number."""
        manager = EncryptionManager()
        phone = "+1234567890"
        
        encrypted = manager.encrypt(phone)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == phone
    
    def test_encrypt_whatsapp_number(self):
        """Test encrypting a WhatsApp number."""
        manager = EncryptionManager()
        whatsapp = "+447700900123"
        
        encrypted = manager.encrypt(whatsapp)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == whatsapp
    
    def test_encrypt_contact_info_all_fields(self):
        """Test encrypting all contact info fields."""
        manager = EncryptionManager()
        
        result = manager.encrypt_contact_info(
            email="user@example.com",
            phone="+1234567890",
            whatsapp="+447700900123"
        )
        
        assert result['email_encrypted'] is not None
        assert result['phone_encrypted'] is not None
        assert result['whatsapp_encrypted'] is not None
    
    def test_encrypt_contact_info_partial(self):
        """Test encrypting partial contact info."""
        manager = EncryptionManager()
        
        result = manager.encrypt_contact_info(
            email="user@example.com",
            phone=None,
            whatsapp=None
        )
        
        assert result['email_encrypted'] is not None
        assert result['phone_encrypted'] is None
        assert result['whatsapp_encrypted'] is None
    
    def test_decrypt_contact_info_all_fields(self):
        """Test decrypting all contact info fields."""
        manager = EncryptionManager()
        
        encrypted = manager.encrypt_contact_info(
            email="user@example.com",
            phone="+1234567890",
            whatsapp="+447700900123"
        )
        
        decrypted = manager.decrypt_contact_info(
            email_encrypted=encrypted['email_encrypted'],
            phone_encrypted=encrypted['phone_encrypted'],
            whatsapp_encrypted=encrypted['whatsapp_encrypted']
        )
        
        assert decrypted['email'] == "user@example.com"
        assert decrypted['phone'] == "+1234567890"
        assert decrypted['whatsapp'] == "+447700900123"
    
    def test_decrypt_contact_info_none_values(self):
        """Test decrypting None values."""
        manager = EncryptionManager()
        
        decrypted = manager.decrypt_contact_info(
            email_encrypted=None,
            phone_encrypted=None,
            whatsapp_encrypted=None
        )
        
        assert decrypted['email'] is None
        assert decrypted['phone'] is None
        assert decrypted['whatsapp'] is None
    
    def test_different_encryptions_for_same_plaintext(self):
        """Test that encrypting the same text multiple times produces different ciphertexts."""
        manager = EncryptionManager()
        plaintext = "test@example.com"
        
        encrypted1 = manager.encrypt(plaintext)
        encrypted2 = manager.encrypt(plaintext)
        
        # Different ciphertexts (Fernet includes timestamp and random IV)
        assert encrypted1 != encrypted2
        
        # Both decrypt to same plaintext
        assert manager.decrypt(encrypted1) == plaintext
        assert manager.decrypt(encrypted2) == plaintext


class TestEmailValidation:
    """Test cases for email validation."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@domain.co.uk") is True
        assert validate_email("admin@company.io") is True
    
    def test_invalid_email_no_at(self):
        """Test invalid email without @ symbol."""
        assert validate_email("userexample.com") is False
    
    def test_invalid_email_no_domain(self):
        """Test invalid email without domain."""
        assert validate_email("user@") is False
    
    def test_invalid_email_no_tld(self):
        """Test invalid email without TLD."""
        assert validate_email("user@domain") is False
    
    def test_invalid_email_empty(self):
        """Test empty email."""
        assert validate_email("") is False
    
    def test_invalid_email_none(self):
        """Test None email."""
        assert validate_email(None) is False


class TestPhoneValidation:
    """Test cases for phone number validation."""
    
    def test_valid_phone_us(self):
        """Test valid US phone number."""
        assert validate_phone("+1234567890") is True
        assert validate_phone("1234567890") is True
    
    def test_valid_phone_uk(self):
        """Test valid UK phone number."""
        assert validate_phone("+447700900123") is True
    
    def test_valid_phone_formatted(self):
        """Test valid formatted phone numbers."""
        assert validate_phone("+1 (234) 567-8900") is True
        assert validate_phone("+1-234-567-8900") is True
    
    def test_invalid_phone_too_short(self):
        """Test invalid phone number (too short)."""
        assert validate_phone("123") is False
        assert validate_phone("+1234") is False
    
    def test_invalid_phone_too_long(self):
        """Test invalid phone number (too long)."""
        assert validate_phone("1234567890123456") is False
    
    def test_invalid_phone_letters(self):
        """Test invalid phone number with letters."""
        assert validate_phone("123-456-ABCD") is False
    
    def test_invalid_phone_empty(self):
        """Test empty phone number."""
        assert validate_phone("") is False
    
    def test_invalid_phone_none(self):
        """Test None phone number."""
        assert validate_phone(None) is False


class TestSanitizeInput:
    """Test cases for input sanitization."""
    
    def test_sanitize_normal_text(self):
        """Test sanitizing normal text."""
        assert sanitize_input("Hello World") == "Hello World"
    
    def test_sanitize_with_whitespace(self):
        """Test sanitizing text with extra whitespace."""
        assert sanitize_input("  Hello World  ") == "Hello World"
    
    def test_sanitize_with_null_bytes(self):
        """Test sanitizing text with null bytes."""
        assert sanitize_input("Hello\x00World") == "HelloWorld"
    
    def test_sanitize_max_length(self):
        """Test sanitizing text exceeding max length."""
        long_text = "A" * 1000
        result = sanitize_input(long_text, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        assert sanitize_input("") == ""
    
    def test_sanitize_none(self):
        """Test sanitizing None."""
        assert sanitize_input(None) == ""
    
    def test_sanitize_special_characters(self):
        """Test sanitizing text with special characters."""
        text = "Hello! @#$% World?"
        assert sanitize_input(text) == "Hello! @#$% World?"
    
    def test_sanitize_unicode(self):
        """Test sanitizing Unicode text."""
        text = "Hello 世界 🌍"
        assert sanitize_input(text) == "Hello 世界 🌍"


class TestEmailHashing:
    """Test cases for email hashing."""
    
    def test_hash_email_consistent(self):
        """Test that hashing same email produces same hash."""
        email = "test@example.com"
        hash1 = hash_email(email)
        hash2 = hash_email(email)
        
        assert hash1 == hash2
    
    def test_hash_email_case_insensitive(self):
        """Test that hashing is case-insensitive."""
        hash1 = hash_email("Test@Example.com")
        hash2 = hash_email("test@example.com")
        
        assert hash1 == hash2
    
    def test_hash_email_different_emails(self):
        """Test that different emails produce different hashes."""
        hash1 = hash_email("user1@example.com")
        hash2 = hash_email("user2@example.com")
        
        assert hash1 != hash2
    
    def test_hash_email_not_reversible(self):
        """Test that hash cannot be reversed to original email."""
        email = "test@example.com"
        hashed = hash_email(email)
        
        # Hash should not contain original email
        assert email not in hashed
        # Hash should be hexadecimal string
        assert all(c in '0123456789abcdef' for c in hashed)
    
    def test_hash_email_deterministic(self):
        """Test that hash is deterministic (SHA-256)."""
        email = "test@example.com"
        hashed = hash_email(email)
        
        # SHA-256 always produces 64 character hex string
        assert len(hashed) == 64
    
    def test_hash_email_strips_whitespace(self):
        """Test that whitespace is stripped before hashing."""
        hash1 = hash_email("  test@example.com  ")
        hash2 = hash_email("test@example.com")
        
        assert hash1 == hash2
