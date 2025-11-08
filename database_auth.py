"""
Multi-user database module for RAAS with authentication support.
Implements users, sessions, and user-specific todos.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from security import EncryptionManager, validate_email, validate_phone, sanitize_input, hash_email

DB_NAME = "todos.db"
encryption_manager = EncryptionManager()


def init_auth_db():
    """Initialize multi-user database with users and sessions tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            name TEXT,
            email_hash TEXT UNIQUE NOT NULL,
            email_encrypted TEXT NOT NULL,
            phone_encrypted TEXT,
            whatsapp_encrypted TEXT,
            auth_provider TEXT DEFAULT 'replit',
            auth_provider_id TEXT UNIQUE,
            consent_email INTEGER DEFAULT 0,
            consent_sms INTEGER DEFAULT 0,
            consent_whatsapp INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Create user_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_fingerprint TEXT,
            issued_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            refresh_token_hash TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_email_hash ON users(email_hash)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_auth_provider_id ON users(auth_provider_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at)
    ''')
    
    # Migration: Add user_id to todos table if it doesn't exist
    # First check if todos table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
    todos_table_exists = cursor.fetchone() is not None
    
    if todos_table_exists:
        try:
            cursor.execute("SELECT user_id FROM todos LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating database: Adding user_id column to todos...")
            cursor.execute("ALTER TABLE todos ADD COLUMN user_id TEXT")
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_todos_user_id ON todos(user_id)
            ''')
            print("Migration complete.")
    
    # Migration: Add UNIQUE constraint to auth_provider_id if not present
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users_table_exists = cursor.fetchone() is not None
    
    if users_table_exists:
        # Check if UNIQUE constraint already exists on auth_provider_id specifically
        # First, check table SQL definition (most reliable method)
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        table_sql = cursor.fetchone()
        has_unique_constraint = False
        
        if table_sql and table_sql[0]:
            # Check if schema contains "auth_provider_id TEXT UNIQUE" (case-insensitive)
            has_unique_constraint = 'AUTH_PROVIDER_ID TEXT UNIQUE' in table_sql[0].upper()
        
        # Fallback: Check PRAGMA index_list for UNIQUE index on auth_provider_id
        if not has_unique_constraint:
            cursor.execute("PRAGMA index_list('users')")
            indexes = cursor.fetchall()
            
            for idx in indexes:
                # idx = (seq, name, unique, origin, partial)
                if idx[2] == 1:  # unique=1
                    # Check which column(s) this index covers
                    cursor.execute(f"PRAGMA index_info('{idx[1]}')")
                    index_columns = cursor.fetchall()
                    # index_columns = [(seqno, cid, name), ...]
                    for col in index_columns:
                        if col[2] and 'auth_provider_id' in col[2].lower():
                            has_unique_constraint = True
                            break
                if has_unique_constraint:
                    break
        
        if not has_unique_constraint:
            print("Migrating database: Adding UNIQUE constraint to auth_provider_id...")
            
            # Step 1: Find and deduplicate any existing duplicates
            cursor.execute('''
                SELECT auth_provider_id, COUNT(*) as cnt
                FROM users
                WHERE auth_provider_id IS NOT NULL
                GROUP BY auth_provider_id
                HAVING cnt > 1
            ''')
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"Found {len(duplicates)} duplicate auth_provider_id entries. Deduplicating...")
                for auth_id, count in duplicates:
                    # Keep the first user, deactivate the rest
                    cursor.execute('''
                        SELECT id FROM users
                        WHERE auth_provider_id = ?
                        ORDER BY created_at ASC
                    ''', (auth_id,))
                    user_ids = [row[0] for row in cursor.fetchall()]
                    
                    if len(user_ids) > 1:
                        print(f"  Keeping user {user_ids[0]}, deactivating {len(user_ids)-1} duplicate(s)")
                        for dup_id in user_ids[1:]:
                            cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (dup_id,))
            
            # Step 2: Rebuild users table with UNIQUE constraint
            # SQLite doesn't support ADD CONSTRAINT, so we need to recreate the table
            print("Rebuilding users table with UNIQUE constraint...")
            
            cursor.execute('''
                CREATE TABLE users_new (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE,
                    name TEXT,
                    email_hash TEXT UNIQUE NOT NULL,
                    email_encrypted TEXT NOT NULL,
                    phone_encrypted TEXT,
                    whatsapp_encrypted TEXT,
                    auth_provider TEXT DEFAULT 'replit',
                    auth_provider_id TEXT UNIQUE,
                    consent_email INTEGER DEFAULT 0,
                    consent_sms INTEGER DEFAULT 0,
                    consent_whatsapp INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Copy data from old table (only active users with unique auth_provider_id)
            # Explicitly list columns to handle missing username/name in old schema
            cursor.execute('''
                INSERT INTO users_new (id, email_hash, email_encrypted, phone_encrypted, whatsapp_encrypted,
                                      auth_provider, auth_provider_id, consent_email, consent_sms, 
                                      consent_whatsapp, created_at, last_login, is_active, username, name)
                SELECT id, email_hash, email_encrypted, phone_encrypted, whatsapp_encrypted,
                       auth_provider, auth_provider_id, consent_email, consent_sms, 
                       consent_whatsapp, created_at, last_login, is_active, NULL, NULL
                FROM users WHERE is_active = 1
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE users')
            cursor.execute('ALTER TABLE users_new RENAME TO users')
            
            # Recreate indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email_hash ON users(email_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_auth_provider_id ON users(auth_provider_id)')
            
            print("Migration complete: UNIQUE constraint applied to auth_provider_id")
    
    # Migration: Add username and name columns if they don't exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users_table_exists = cursor.fetchone() is not None
    
    if users_table_exists:
        try:
            cursor.execute("SELECT username FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Migrating database: Adding username and name columns...")
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
            # Note: UNIQUE constraint on username will be enforced at application level for existing rows
            print("Migration complete: username and name columns added")
    
    conn.commit()
    conn.close()


def create_user(email: str, auth_provider: str = 'replit', 
                auth_provider_id: Optional[str] = None,
                username: Optional[str] = None,
                name: Optional[str] = None,
                phone: Optional[str] = None, 
                whatsapp: Optional[str] = None,
                consent_email: bool = False,
                consent_sms: bool = False,
                consent_whatsapp: bool = False) -> Optional[str]:
    """
    Create a new user with encrypted contact information.
    
    Args:
        email: User's email (plaintext, will be stored encrypted)
        auth_provider: Authentication provider (default: 'replit')
        auth_provider_id: External provider user ID
        phone: Phone number (optional, will be encrypted)
        whatsapp: WhatsApp number (optional, will be encrypted)
        consent_email: User consent for email notifications
        consent_sms: User consent for SMS notifications
        consent_whatsapp: User consent for WhatsApp notifications
    
    Returns:
        User ID (UUID) if successful, None otherwise
    """
    # Validate inputs
    if not validate_email(email):
        print(f"Invalid email format: {email}")
        return None
    
    if phone and not validate_phone(phone):
        print(f"Invalid phone format: {phone}")
        return None
    
    if whatsapp and not validate_phone(whatsapp):
        print(f"Invalid WhatsApp format: {whatsapp}")
        return None
    
    # Application-level guard: Check if auth_provider_id already exists
    # This prevents duplicates even if UNIQUE constraint hasn't been applied yet
    if auth_provider_id:
        existing_user = get_user_by_auth_id(auth_provider_id)
        if existing_user:
            print(f"User already exists with auth_provider_id {auth_provider_id}, returning existing user")
            return existing_user['id']
    
    # Sanitize inputs
    email = sanitize_input(email, max_length=255)
    if username:
        username = sanitize_input(username, max_length=100)
    if name:
        name = sanitize_input(name, max_length=255)
    
    # Hash email for lookups (never store plaintext email!)
    email_hashed = hash_email(email)
    
    # Encrypt contact information for storage
    encrypted_data = encryption_manager.encrypt_contact_info(
        email=email,
        phone=phone,
        whatsapp=whatsapp
    )
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        user_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO users (id, username, name, email_hash, email_encrypted, phone_encrypted, whatsapp_encrypted,
                             auth_provider, auth_provider_id, consent_email, consent_sms, 
                             consent_whatsapp, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, name, email_hashed, encrypted_data['email_encrypted'], 
              encrypted_data['phone_encrypted'], encrypted_data['whatsapp_encrypted'],
              auth_provider, auth_provider_id,
              1 if consent_email else 0, 1 if consent_sms else 0, 
              1 if consent_whatsapp else 0, datetime.now().isoformat()))
        
        conn.commit()
        print(f"User created successfully: {user_id}")
        return user_id
    
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        # If duplicate auth_provider_id, return existing user's ID
        if 'auth_provider_id' in error_msg and auth_provider_id:
            print(f"User already exists with auth_provider_id {auth_provider_id}, returning existing user")
            # Get existing user by auth_provider_id
            existing_user = get_user_by_auth_id(auth_provider_id)
            return existing_user['id'] if existing_user else None
        else:
            # Duplicate email or other constraint violation
            print(f"User creation failed (duplicate email?): {e}")
            return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email address (uses hashed lookup)."""
    # Hash the email for lookup
    email_hashed = hash_email(email)
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email_hash = ? AND is_active = 1', (email_hashed,))
    row = cursor.fetchone()
    
    user = dict(row) if row else None
    conn.close()
    
    # Decrypt contact info if user exists
    if user:
        decrypted = encryption_manager.decrypt_contact_info(
            email_encrypted=user.get('email_encrypted'),
            phone_encrypted=user.get('phone_encrypted'),
            whatsapp_encrypted=user.get('whatsapp_encrypted')
        )
        user['email_decrypted'] = decrypted['email']
        user['phone_decrypted'] = decrypted['phone']
        user['whatsapp_decrypted'] = decrypted['whatsapp']
    
    return user


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (user_id,))
    row = cursor.fetchone()
    
    user = dict(row) if row else None
    conn.close()
    
    # Decrypt contact info if user exists
    if user:
        decrypted = encryption_manager.decrypt_contact_info(
            email_encrypted=user.get('email_encrypted'),
            phone_encrypted=user.get('phone_encrypted'),
            whatsapp_encrypted=user.get('whatsapp_encrypted')
        )
        user['email_decrypted'] = decrypted['email']
        user['phone_decrypted'] = decrypted['phone']
        user['whatsapp_decrypted'] = decrypted['whatsapp']
    
    return user


def get_user_by_auth_id(auth_provider_id: str) -> Optional[Dict]:
    """
    Get user by authentication provider ID (e.g., Replit user ID).
    
    Args:
        auth_provider_id: External authentication provider's user ID
        
    Returns:
        User dictionary with decrypted contact info, or None if not found
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE auth_provider_id = ? AND is_active = 1', (auth_provider_id,))
    row = cursor.fetchone()
    
    user = dict(row) if row else None
    conn.close()
    
    # Decrypt contact info if user exists
    if user:
        decrypted = encryption_manager.decrypt_contact_info(
            email_encrypted=user.get('email_encrypted'),
            phone_encrypted=user.get('phone_encrypted'),
            whatsapp_encrypted=user.get('whatsapp_encrypted')
        )
        user['email_decrypted'] = decrypted['email']
        user['phone_decrypted'] = decrypted['phone']
        user['whatsapp_decrypted'] = decrypted['whatsapp']
    
    return user


def get_all_users() -> List[Dict]:
    """
    Get all active users.
    
    Returns:
        List of user dictionaries with decrypted contact info
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY created_at ASC')
    rows = cursor.fetchall()
    
    users = []
    for row in rows:
        user = dict(row)
        # Decrypt contact info
        decrypted = encryption_manager.decrypt_contact_info(
            email_encrypted=user.get('email_encrypted'),
            phone_encrypted=user.get('phone_encrypted'),
            whatsapp_encrypted=user.get('whatsapp_encrypted')
        )
        user['email_decrypted'] = decrypted['email']
        user['phone_decrypted'] = decrypted['phone']
        user['whatsapp_decrypted'] = decrypted['whatsapp']
        users.append(user)
    
    conn.close()
    return users


def update_user_contact_info(user_id: str, email: Optional[str] = None,
                             phone: Optional[str] = None, 
                             whatsapp: Optional[str] = None) -> bool:
    """
    Update user's contact information (encrypted).
    
    Args:
        user_id: User's ID
        email: New email (optional)
        phone: New phone (optional)
        whatsapp: New WhatsApp (optional)
    
    Returns:
        True if successful, False otherwise
    """
    # Get current user data
    user = get_user_by_id(user_id)
    if not user:
        return False
    
    # Use existing values if not provided
    email = email or user.get('email_decrypted')
    phone = phone or user.get('phone_decrypted')
    whatsapp = whatsapp or user.get('whatsapp_decrypted')
    
    # Validate
    if email and not validate_email(email):
        return False
    if phone and not validate_phone(phone):
        return False
    if whatsapp and not validate_phone(whatsapp):
        return False
    
    # Hash new email if provided
    email_hashed = hash_email(email) if email else user.get('email_hash')
    
    # Encrypt
    encrypted_data = encryption_manager.encrypt_contact_info(
        email=email,
        phone=phone,
        whatsapp=whatsapp
    )
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users 
            SET email_hash = ?, email_encrypted = ?, phone_encrypted = ?, whatsapp_encrypted = ?
            WHERE id = ?
        ''', (email_hashed, encrypted_data['email_encrypted'], 
              encrypted_data['phone_encrypted'], encrypted_data['whatsapp_encrypted'], user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Update failed: {e}")
        return False
    finally:
        conn.close()


def create_session(user_id: str, device_fingerprint: Optional[str] = None,
                   expires_in_days: int = 30) -> Optional[str]:
    """
    Create a new session for a user.
    
    Args:
        user_id: User's ID
        device_fingerprint: Optional device identifier
        expires_in_days: Session expiration (default: 30 days)
    
    Returns:
        Session ID if successful, None otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    session_id = str(uuid.uuid4())
    expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO user_sessions (session_id, user_id, device_fingerprint, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, device_fingerprint, expires_at))
        
        # Update last_login
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        conn.commit()
        return session_id
    except Exception as e:
        print(f"Session creation failed: {e}")
        return None
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID and check if valid."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM user_sessions 
        WHERE session_id = ? AND is_active = 1
    ''', (session_id,))
    
    row = cursor.fetchone()
    session = dict(row) if row else None
    conn.close()
    
    # Check expiration
    if session:
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            invalidate_session(session_id)
            return None
    
    return session


def invalidate_session(session_id: str) -> bool:
    """Invalidate a session."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE session_id = ?
        ''', (session_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Session invalidation failed: {e}")
        return False
    finally:
        conn.close()


def cleanup_expired_sessions():
    """Remove expired sessions from database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM user_sessions 
        WHERE datetime(expires_at) < datetime('now')
    ''')
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count
