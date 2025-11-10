"""
Multi-User Test Suite for RAAS
Tests user authentication, data isolation, and profile updates across different users
"""

import pytest
from database_auth import create_user, get_user_by_id, get_user_by_auth_id, update_user_profile, update_user_contact_info
from database_multi_user import (
    add_todo_for_user, 
    get_todos_for_user, 
    update_todo_for_user,
    delete_todo_for_user
)
import database_auth
import database_multi_user
import uuid


def generate_unique_id(prefix="test"):
    """Generate a unique ID for test users"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class TestMultiUserAuthentication:
    """Test user creation and authentication"""
    
    def test_create_multiple_users(self):
        """Test creating multiple users with different credentials"""
        # Use unique IDs for each test run
        auth_id_1 = generate_unique_id("user1")
        auth_id_2 = generate_unique_id("user2")
        auth_id_3 = generate_unique_id("user3")
        
        # User 1
        user1_id = create_user(
            email=f"{auth_id_1}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_1,
            username=f"testuser_{auth_id_1}",
            name="Test User One",
            phone="+11234567890",
            consent_email=True,
            consent_sms=True
        )
        assert user1_id is not None, "Failed to create user 1"
        
        # User 2
        user2_id = create_user(
            email=f"{auth_id_2}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_2,
            username=f"testuser_{auth_id_2}",
            name="Test User Two",
            whatsapp="+19876543210",
            consent_email=True,
            consent_whatsapp=True
        )
        assert user2_id is not None, "Failed to create user 2"
        
        # User 3 - only email
        user3_id = create_user(
            email=f"{auth_id_3}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_3,
            username=f"testuser_{auth_id_3}",
            name="Test User Three",
            consent_email=True
        )
        assert user3_id is not None, "Failed to create user 3"
        
        # Verify all users are different
        assert user1_id != user2_id != user3_id
        
        print(f"✅ Created 3 users: {user1_id}, {user2_id}, {user3_id}")
        return user1_id, user2_id, user3_id
    
    def test_user_login_retrieval(self):
        """Test retrieving users by their auth provider ID (simulating login)"""
        # Create new test users
        auth_id_1 = generate_unique_id("login1")
        auth_id_2 = generate_unique_id("login2")
        
        user1_id = create_user(
            email=f"{auth_id_1}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_1,
            username=f"loginuser_{auth_id_1}",
            name="Login Test User 1",
            consent_email=True
        )
        
        user2_id = create_user(
            email=f"{auth_id_2}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_2,
            username=f"loginuser_{auth_id_2}",
            name="Login Test User 2",
            consent_email=True
        )
        
        # Login as user 1
        user1 = get_user_by_auth_id(auth_id_1)
        assert user1 is not None, "User 1 not found"
        assert user1['id'] == user1_id
        
        # Login as user 2
        user2 = get_user_by_auth_id(auth_id_2)
        assert user2 is not None, "User 2 not found"
        assert user2['id'] == user2_id
        
        print("✅ All users can log in successfully")
        return user1_id, user2_id
    
    def test_duplicate_username_rejection(self):
        """Test that duplicate usernames are rejected"""
        # Use unique username for testing
        unique_username = f"duptest_{generate_unique_id('dup')}"
        auth_id_1 = generate_unique_id("dup1")
        auth_id_2 = generate_unique_id("dup2")
        
        # Create first user
        user1_id = create_user(
            email=f"{auth_id_1}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_1,
            username=unique_username,
            name="First User",
            consent_email=True
        )
        assert user1_id is not None
        
        # Try to create second user with same username - database should reject via UNIQUE constraint
        user2_id = create_user(
            email=f"{auth_id_2}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_2,
            username=unique_username,  # Same username
            name="Second User",
            consent_email=True
        )
        # The database should reject duplicate usernames via UNIQUE constraint
        # create_user handles IntegrityError and returns 'DUPLICATE_USERNAME' for duplicates
        assert user2_id == 'DUPLICATE_USERNAME', f"Duplicate username '{unique_username}' should be rejected but got: {user2_id}"
        print("✅ Duplicate username correctly rejected")


class TestDataIsolation:
    """Test that users cannot see each other's data"""
    
    def test_todo_isolation(self):
        """Test that each user only sees their own todos"""
        from datetime import datetime, timedelta
        
        # Create 2 users with unique IDs
        auth_id_1 = generate_unique_id("isolated1")
        auth_id_2 = generate_unique_id("isolated2")
        
        user1_id = create_user(
            email=f"{auth_id_1}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_1,
            username=f"isolated_user_{auth_id_1}",
            name="Isolated User 1",
            consent_email=True
        )
        
        user2_id = create_user(
            email=f"{auth_id_2}@test.com",
            auth_provider="replit",
            auth_provider_id=auth_id_2,
            username=f"isolated_user_{auth_id_2}",
            name="Isolated User 2",
            consent_email=True
        )
        
        # User 1 creates 3 todos
        due_date = (datetime.now() + timedelta(days=1)).isoformat()
        todo1_1 = add_todo_for_user(user1_id, "User 1 Task 1", "", due_date, "", "", "")
        todo1_2 = add_todo_for_user(user1_id, "User 1 Task 2", "", due_date, "", "", "")
        todo1_3 = add_todo_for_user(user1_id, "User 1 Task 3", "", due_date, "", "", "")
        
        # User 2 creates 2 todos
        todo2_1 = add_todo_for_user(user2_id, "User 2 Task 1", "", due_date, "", "", "")
        todo2_2 = add_todo_for_user(user2_id, "User 2 Task 2", "", due_date, "", "", "")
        
        # Get todos for each user
        user1_todos = get_todos_for_user(user1_id)
        user2_todos = get_todos_for_user(user2_id)
        
        # Verify user 1 only sees their 3 todos
        assert len(user1_todos) == 3, f"User 1 should have 3 todos, got {len(user1_todos)}"
        user1_titles = [t['title'] for t in user1_todos]
        assert "User 1 Task 1" in user1_titles
        assert "User 2 Task 1" not in user1_titles, "User 1 should NOT see User 2's todos"
        
        # Verify user 2 only sees their 2 todos
        assert len(user2_todos) == 2, f"User 2 should have 2 todos, got {len(user2_todos)}"
        user2_titles = [t['title'] for t in user2_todos]
        assert "User 2 Task 1" in user2_titles
        assert "User 1 Task 1" not in user2_titles, "User 2 should NOT see User 1's todos"
        
        print(f"✅ Data isolation working: User 1 has {len(user1_todos)} todos, User 2 has {len(user2_todos)} todos")


class TestProfileUpdates:
    """Test profile updates for different users"""
    
    def test_independent_profile_updates(self):
        """Test that updating one user's profile doesn't affect other users"""
        # Create 2 users
        user1_id = create_user(
            email="update1@test.com",
            auth_provider="replit",
            auth_provider_id="update_1",
            username="update_user1",
            name="Original Name 1",
            phone="+11111111111",
            consent_email=True
        )
        
        user2_id = create_user(
            email="update2@test.com",
            auth_provider="replit",
            auth_provider_id="update_2",
            username="update_user2",
            name="Original Name 2",
            phone="+12222222222",
            consent_email=True
        )
        
        # Update User 1's profile
        success1 = update_user_profile(user1_id, name="Updated Name 1", username="new_username1")
        assert success1, "Failed to update user 1 profile"
        
        # Update User 1's contact info
        success2 = update_user_contact_info(user1_id, email="newemail1@test.com", phone="+13333333333")
        assert success2, "Failed to update user 1 contact info"
        
        # Verify User 1's updates
        user1_updated = get_user_by_id(user1_id)
        assert user1_updated['name'] == "Updated Name 1"
        assert user1_updated['username'] == "new_username1"
        assert user1_updated['email_decrypted'] == "newemail1@test.com"
        assert user1_updated['phone_decrypted'] == "+13333333333"
        
        # Verify User 2 remains unchanged
        user2_unchanged = get_user_by_id(user2_id)
        assert user2_unchanged['name'] == "Original Name 2", "User 2's name should not change"
        assert user2_unchanged['username'] == "update_user2", "User 2's username should not change"
        assert user2_unchanged['email_decrypted'] == "update2@test.com"
        assert user2_unchanged['phone_decrypted'] == "+12222222222"
        
        print("✅ Profile updates are isolated - User 1 updated, User 2 unchanged")
    
    def test_update_all_users_independently(self):
        """Test updating multiple users' profiles independently"""
        # Create 3 users
        users = []
        for i in range(1, 4):
            user_id = create_user(
                email=f"multi{i}@test.com",
                auth_provider="replit",
                auth_provider_id=f"multi_{i}",
                username=f"multiuser{i}",
                name=f"Multi User {i}",
                consent_email=True
            )
            users.append(user_id)
        
        # Update each user with different information
        for i, user_id in enumerate(users, 1):
            update_user_profile(user_id, name=f"Updated Multi User {i}")
            update_user_contact_info(user_id, email=f"updated{i}@test.com")
        
        # Verify each user has their correct updated information
        for i, user_id in enumerate(users, 1):
            user = get_user_by_id(user_id)
            assert user['name'] == f"Updated Multi User {i}"
            assert user['email_decrypted'] == f"updated{i}@test.com"
        
        print(f"✅ All {len(users)} users updated independently with correct data")


class TestOnboardingValidation:
    """Test onboarding validation requirements"""
    
    def test_require_email(self):
        """Test that email is required (database constraint)"""
        # Try to create user without email - should fail at database level
        # This tests the backend constraint, not just form validation
        auth_id = generate_unique_id("noemail")
        
        user_id = create_user(
            email=None,  # No email - violates database NOT NULL constraint
            auth_provider="replit",
            auth_provider_id=auth_id,
            username=f"noemail_{auth_id}",
            name="No Email User",
            phone="+18888888888",
            consent_sms=True
        )
        # Database should reject this (email_hash and email_encrypted are NOT NULL)
        assert user_id is None, "User creation without email should fail (database constraint)"
        
        print("✅ Email is correctly required at database level")
    
    def test_valid_user_with_single_contact_method(self):
        """Test creating users with different contact method combinations"""
        # User with only email (minimum requirement)
        email_user = create_user(
            email="onlyemail@test.com",
            auth_provider="replit",
            auth_provider_id="email_only",
            username="emailonlyuser",
            name="Email Only User",
            consent_email=True
        )
        assert email_user is not None
        
        # User with email + phone
        phone_user = create_user(
            email="withphone@test.com",
            auth_provider="replit",
            auth_provider_id="phone_also",
            username="phonealsouser",
            name="Email and Phone User",
            phone="+14444444444",
            consent_email=True,
            consent_sms=True
        )
        assert phone_user is not None
        
        # User with email + WhatsApp
        whatsapp_user = create_user(
            email="withwhatsapp@test.com",
            auth_provider="replit",
            auth_provider_id="whatsapp_also",
            username="whatsappalsouser",
            name="Email and WhatsApp User",
            whatsapp="+15555555555",
            consent_email=True,
            consent_whatsapp=True
        )
        assert whatsapp_user is not None
        
        # User with all three methods
        all_methods_user = create_user(
            email="allmethods@test.com",
            auth_provider="replit",
            auth_provider_id="all_methods",
            username="allmethodsuser",
            name="All Methods User",
            phone="+16666666666",
            whatsapp="+17777777777",
            consent_email=True,
            consent_sms=True,
            consent_whatsapp=True
        )
        assert all_methods_user is not None
        
        print("✅ Users can be created with various contact method combinations")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("🧪 RAAS MULTI-USER TEST SUITE")
    print("="*80 + "\n")
    
    # Clean up test data first (optional)
    print("⚠️  Note: Running tests on development database\n")
    
    # Test Authentication
    print("\n📝 Testing Multi-User Authentication...")
    auth_tests = TestMultiUserAuthentication()
    auth_tests.test_create_multiple_users()
    auth_tests.test_user_login_retrieval()
    auth_tests.test_duplicate_username_rejection()
    
    # Test Data Isolation
    print("\n🔒 Testing Data Isolation...")
    isolation_tests = TestDataIsolation()
    isolation_tests.test_todo_isolation()
    
    # Test Profile Updates
    print("\n✏️  Testing Profile Updates...")
    update_tests = TestProfileUpdates()
    update_tests.test_independent_profile_updates()
    update_tests.test_update_all_users_independently()
    
    # Test Onboarding
    print("\n📋 Testing Onboarding Validation...")
    onboarding_tests = TestOnboardingValidation()
    onboarding_tests.test_require_email()
    onboarding_tests.test_valid_user_with_single_contact_method()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()
