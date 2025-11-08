"""
Unit tests for database_auth.py - Multi-user database with authentication.
"""

import pytest
import os
import sqlite3
from datetime import datetime, timedelta
from database_auth import (
    init_auth_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_contact_info,
    create_session,
    get_session,
    invalidate_session,
    cleanup_expired_sessions,
    DB_NAME
)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    test_db_name = "test_auth_todos.db"
    
    # Override DB_NAME globally
    import database_auth
    original_db = database_auth.DB_NAME
    database_auth.DB_NAME = test_db_name
    
    # Initialize database
    init_auth_db()
    
    yield test_db_name
    
    # Cleanup
    database_auth.DB_NAME = original_db
    if os.path.exists(test_db_name):
        os.remove(test_db_name)


class TestDatabaseInit:
    """Test database initialization."""
    
    def test_init_creates_users_table(self, test_db):
        """Test that init_auth_db creates users table."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'users'
        conn.close()
    
    def test_init_creates_sessions_table(self, test_db):
        """Test that init_auth_db creates user_sessions table."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'user_sessions'
        conn.close()
    
    def test_users_table_has_required_columns(self, test_db):
        """Test users table has all required columns."""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = ['id', 'email_hash', 'email_encrypted', 'phone_encrypted', 
                          'whatsapp_encrypted', 'auth_provider', 'created_at', 'last_login']
        
        for col in required_columns:
            assert col in columns
        
        # Ensure plaintext email column does NOT exist
        assert 'email' not in columns or 'email' == 'email_hash' or 'email' == 'email_encrypted'
        
        conn.close()


class TestCreateUser:
    """Test user creation."""
    
    def test_create_user_basic(self, test_db):
        """Test creating a basic user with email only."""
        user_id = create_user(email="test@example.com")
        
        assert user_id is not None
        assert len(user_id) == 36  # UUID format
    
    def test_create_user_with_all_contact_info(self, test_db):
        """Test creating a user with all contact information."""
        user_id = create_user(
            email="test@example.com",
            phone="+1234567890",
            whatsapp="+447700900123",
            consent_email=True,
            consent_sms=True,
            consent_whatsapp=True
        )
        
        assert user_id is not None
        
        # Verify stored correctly
        user = get_user_by_id(user_id)
        assert user is not None
        assert user['email_decrypted'] == "test@example.com"
        assert user['phone_decrypted'] == "+1234567890"
        assert user['whatsapp_decrypted'] == "+447700900123"
        assert user['consent_email'] == 1
        assert user['consent_sms'] == 1
        assert user['consent_whatsapp'] == 1
    
    def test_create_user_duplicate_email(self, test_db):
        """Test that duplicate emails are rejected."""
        create_user(email="test@example.com")
        duplicate_user_id = create_user(email="test@example.com")
        
        assert duplicate_user_id is None
    
    def test_create_user_invalid_email(self, test_db):
        """Test creating user with invalid email."""
        user_id = create_user(email="invalid-email")
        
        assert user_id is None
    
    def test_create_user_invalid_phone(self, test_db):
        """Test creating user with invalid phone number."""
        user_id = create_user(
            email="test@example.com",
            phone="invalid"
        )
        
        assert user_id is None
    
    def test_contact_info_is_encrypted(self, test_db):
        """Test that contact info is stored encrypted in database."""
        user_id = create_user(
            email="test@example.com",
            phone="+1234567890"
        )
        
        # Query database directly
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT email_hash, email_encrypted, phone_encrypted FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        # Email should be hashed (not plaintext)
        assert row[0] is not None
        assert row[0] != "test@example.com"
        assert len(row[0]) == 64  # SHA-256 hash length
        
        # Encrypted values should not match plaintext
        assert row[1] is not None
        assert row[1] != "test@example.com"
        assert row[2] is not None
        assert row[2] != "+1234567890"
    
    def test_consent_defaults_to_false(self, test_db):
        """Test that consent flags default to False (GDPR compliance)."""
        user_id = create_user(email="test@example.com")
        
        user = get_user_by_id(user_id)
        assert user['consent_email'] == 0
        assert user['consent_sms'] == 0
        assert user['consent_whatsapp'] == 0


class TestGetUser:
    """Test user retrieval."""
    
    def test_get_user_by_email(self, test_db):
        """Test retrieving user by email (via hash lookup)."""
        user_id = create_user(email="test@example.com")
        
        user = get_user_by_email("test@example.com")
        
        assert user is not None
        assert user['id'] == user_id
        assert user['email_decrypted'] == "test@example.com"
    
    def test_get_user_by_email_case_insensitive(self, test_db):
        """Test that email lookup is case-insensitive."""
        user_id = create_user(email="Test@Example.COM")
        
        # Should find user regardless of case
        user1 = get_user_by_email("test@example.com")
        user2 = get_user_by_email("TEST@EXAMPLE.COM")
        user3 = get_user_by_email("Test@Example.COM")
        
        assert user1 is not None
        assert user2 is not None
        assert user3 is not None
        assert user1['id'] == user_id
        assert user2['id'] == user_id
        assert user3['id'] == user_id
    
    def test_get_user_by_email_not_found(self, test_db):
        """Test retrieving non-existent user."""
        user = get_user_by_email("nonexistent@example.com")
        
        assert user is None
    
    def test_get_user_by_id(self, test_db):
        """Test retrieving user by ID."""
        user_id = create_user(email="test@example.com")
        
        user = get_user_by_id(user_id)
        
        assert user is not None
        assert user['id'] == user_id
        assert user['email_decrypted'] == "test@example.com"
    
    def test_get_user_by_id_not_found(self, test_db):
        """Test retrieving user with invalid ID."""
        user = get_user_by_id("nonexistent-id")
        
        assert user is None
    
    def test_get_user_decrypts_contact_info(self, test_db):
        """Test that get_user decrypts contact information."""
        user_id = create_user(
            email="test@example.com",
            phone="+1234567890",
            whatsapp="+447700900123"
        )
        
        user = get_user_by_id(user_id)
        
        assert user['email_decrypted'] == "test@example.com"
        assert user['phone_decrypted'] == "+1234567890"
        assert user['whatsapp_decrypted'] == "+447700900123"


class TestUpdateUser:
    """Test user updates."""
    
    def test_update_user_phone(self, test_db):
        """Test updating user's phone number."""
        user_id = create_user(email="test@example.com")
        
        success = update_user_contact_info(
            user_id=user_id,
            phone="+1987654321"
        )
        
        assert success is True
        
        user = get_user_by_id(user_id)
        assert user['phone_decrypted'] == "+1987654321"
    
    def test_update_user_whatsapp(self, test_db):
        """Test updating user's WhatsApp number."""
        user_id = create_user(email="test@example.com")
        
        success = update_user_contact_info(
            user_id=user_id,
            whatsapp="+447700900456"
        )
        
        assert success is True
        
        user = get_user_by_id(user_id)
        assert user['whatsapp_decrypted'] == "+447700900456"
    
    def test_update_user_invalid_email(self, test_db):
        """Test updating with invalid email."""
        user_id = create_user(email="test@example.com")
        
        success = update_user_contact_info(
            user_id=user_id,
            email="invalid-email"
        )
        
        assert success is False
    
    def test_update_nonexistent_user(self, test_db):
        """Test updating non-existent user."""
        success = update_user_contact_info(
            user_id="nonexistent-id",
            phone="+1234567890"
        )
        
        assert success is False


class TestSessions:
    """Test session management."""
    
    def test_create_session(self, test_db):
        """Test creating a session."""
        user_id = create_user(email="test@example.com")
        session_id = create_session(user_id=user_id)
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
    
    def test_get_session(self, test_db):
        """Test retrieving a session."""
        user_id = create_user(email="test@example.com")
        session_id = create_session(user_id=user_id)
        
        session = get_session(session_id)
        
        assert session is not None
        assert session['user_id'] == user_id
        assert session['is_active'] == 1
    
    def test_get_session_not_found(self, test_db):
        """Test retrieving non-existent session."""
        session = get_session("nonexistent-session-id")
        
        assert session is None
    
    def test_session_with_device_fingerprint(self, test_db):
        """Test creating session with device fingerprint."""
        user_id = create_user(email="test@example.com")
        session_id = create_session(
            user_id=user_id,
            device_fingerprint="device123"
        )
        
        session = get_session(session_id)
        assert session['device_fingerprint'] == "device123"
    
    def test_invalidate_session(self, test_db):
        """Test invalidating a session."""
        user_id = create_user(email="test@example.com")
        session_id = create_session(user_id=user_id)
        
        success = invalidate_session(session_id)
        assert success is True
        
        session = get_session(session_id)
        assert session is None
    
    def test_expired_session_returns_none(self, test_db):
        """Test that expired sessions return None."""
        user_id = create_user(email="test@example.com")
        
        # Create session with very short expiration
        session_id = create_session(user_id=user_id, expires_in_days=-1)
        
        session = get_session(session_id)
        assert session is None
    
    def test_cleanup_expired_sessions(self, test_db):
        """Test cleanup of expired sessions."""
        user_id = create_user(email="test@example.com")
        
        # Create expired session
        create_session(user_id=user_id, expires_in_days=-1)
        
        # Create active session
        create_session(user_id=user_id, expires_in_days=30)
        
        deleted_count = cleanup_expired_sessions()
        assert deleted_count >= 1
