"""
Migration Utility for Legacy Todos

Handles migration of NULL user_id todos from the single-user system
to the multi-user system by assigning them to specific users.
"""

import sqlite3
import database
import database_auth
from typing import Optional, List, Dict
from datetime import datetime


def get_legacy_todos_count() -> int:
    """
    Count todos with NULL user_id (legacy single-user todos).
    
    Returns:
        Number of legacy todos
    """
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM todos WHERE user_id IS NULL')
    count = cursor.fetchone()[0]
    
    conn.close()
    return count


def get_legacy_todos() -> List[Dict]:
    """
    Get all todos with NULL user_id.
    
    Returns:
        List of legacy todo dictionaries
    """
    conn = sqlite3.connect(database.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM todos WHERE user_id IS NULL ORDER BY created_at ASC')
    todos = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return todos


def assign_legacy_todos_to_user(user_id: str, dry_run: bool = True) -> Dict:
    """
    Assign all NULL user_id todos to a specific user.
    
    Args:
        user_id: The user ID to assign todos to
        dry_run: If True, only simulate (don't actually update). Default True.
        
    Returns:
        Dict with migration statistics
    """
    # Verify user exists
    user = database_auth.get_user_by_auth_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found in database. User must complete onboarding first.")
    
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    # Get count before
    cursor.execute('SELECT COUNT(*) FROM todos WHERE user_id IS NULL')
    legacy_count = cursor.fetchone()[0]
    
    if legacy_count == 0:
        conn.close()
        return {
            'status': 'no_action_needed',
            'legacy_todos_found': 0,
            'todos_migrated': 0,
            'dry_run': dry_run
        }
    
    if not dry_run:
        # Perform the actual migration
        cursor.execute('''
            UPDATE todos 
            SET user_id = ? 
            WHERE user_id IS NULL
        ''', (user_id,))
        
        conn.commit()
        migrated_count = cursor.rowcount
    else:
        migrated_count = legacy_count
    
    conn.close()
    
    return {
        'status': 'success' if not dry_run else 'dry_run_success',
        'legacy_todos_found': legacy_count,
        'todos_migrated': migrated_count,
        'assigned_to_user': user_id,
        'dry_run': dry_run
    }


def delete_legacy_todos(dry_run: bool = True) -> Dict:
    """
    Delete all NULL user_id todos (use with caution!).
    
    Args:
        dry_run: If True, only simulate (don't actually delete). Default True.
        
    Returns:
        Dict with deletion statistics
    """
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    # Get count before
    cursor.execute('SELECT COUNT(*) FROM todos WHERE user_id IS NULL')
    legacy_count = cursor.fetchone()[0]
    
    if legacy_count == 0:
        conn.close()
        return {
            'status': 'no_action_needed',
            'legacy_todos_found': 0,
            'todos_deleted': 0,
            'dry_run': dry_run
        }
    
    if not dry_run:
        # Perform the actual deletion
        cursor.execute('DELETE FROM todos WHERE user_id IS NULL')
        conn.commit()
        deleted_count = cursor.rowcount
    else:
        deleted_count = legacy_count
    
    conn.close()
    
    return {
        'status': 'success' if not dry_run else 'dry_run_success',
        'legacy_todos_found': legacy_count,
        'todos_deleted': deleted_count,
        'dry_run': dry_run
    }


def migrate_legacy_todos_interactive():
    """
    Interactive CLI for migrating legacy todos.
    
    Provides options to:
    1. View legacy todos
    2. Assign to a user
    3. Delete legacy todos
    """
    print("\n" + "="*60)
    print("RAAS Legacy Todo Migration Utility")
    print("="*60)
    
    # Check for legacy todos
    legacy_count = get_legacy_todos_count()
    
    if legacy_count == 0:
        print("\n✅ No legacy todos found. All todos have user_id assigned.")
        print("   Migration not needed.")
        return
    
    print(f"\n⚠️  Found {legacy_count} legacy todos with NULL user_id")
    print("   These are from the single-user version of RAAS.")
    
    # Get all users
    users = database_auth.get_all_users()
    
    if not users:
        print("\n❌ No users found in the system!")
        print("   At least one user must complete onboarding before migration.")
        return
    
    print(f"\n📋 Available users ({len(users)}):")
    for i, user in enumerate(users, 1):
        print(f"   {i}. {user['auth_provider_id']} - {user.get('username', 'N/A')}")
    
    print("\n🔧 Migration Options:")
    print("   1. View legacy todos")
    print("   2. Assign all legacy todos to a user")
    print("   3. Delete all legacy todos (CAUTION!)")
    print("   4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # View legacy todos
        todos = get_legacy_todos()
        print(f"\n📄 Legacy Todos ({len(todos)}):\n")
        for i, todo in enumerate(todos, 1):
            print(f"{i}. [{todo['priority']}] {todo['title']}")
            print(f"   Due: {todo['due_date']}")
            print(f"   Created: {todo.get('created_at', 'Unknown')}")
            print(f"   Category: {todo.get('category', 'None')}")
            print()
        
        # Ask if they want to continue
        cont = input("Continue with migration? (y/n): ").strip().lower()
        if cont == 'y':
            migrate_legacy_todos_interactive()  # Recursive call
    
    elif choice == "2":
        # Assign to user
        print("\nSelect user to assign todos to:")
        for i, user in enumerate(users, 1):
            print(f"   {i}. {user['auth_provider_id']} - {user.get('username', 'N/A')}")
        
        user_choice = input(f"\nEnter user number (1-{len(users)}): ").strip()
        
        try:
            user_index = int(user_choice) - 1
            if 0 <= user_index < len(users):
                selected_user = users[user_index]
                user_id = selected_user['auth_provider_id']
                
                # Dry run first
                print(f"\n🔍 Dry run: Simulating assignment to {user_id}...")
                result = assign_legacy_todos_to_user(user_id, dry_run=True)
                print(f"   Would migrate {result['todos_migrated']} todos")
                
                confirm = input("\n⚠️  Proceed with actual migration? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    result = assign_legacy_todos_to_user(user_id, dry_run=False)
                    print(f"\n✅ Success! Migrated {result['todos_migrated']} todos to user {user_id}")
                else:
                    print("\n❌ Migration cancelled.")
            else:
                print("\n❌ Invalid user number.")
        except ValueError:
            print("\n❌ Invalid input.")
    
    elif choice == "3":
        # Delete legacy todos
        print("\n⚠️  WARNING: This will permanently delete all legacy todos!")
        print("   This action CANNOT be undone.")
        
        # Dry run first
        result = delete_legacy_todos(dry_run=True)
        print(f"\n🔍 Would delete {result['todos_deleted']} todos")
        
        confirm1 = input("\n⚠️  Type 'DELETE' to confirm deletion: ").strip()
        if confirm1 == 'DELETE':
            confirm2 = input("   Type 'CONFIRM' to proceed: ").strip()
            if confirm2 == 'CONFIRM':
                result = delete_legacy_todos(dry_run=False)
                print(f"\n✅ Deleted {result['todos_deleted']} legacy todos")
            else:
                print("\n❌ Deletion cancelled.")
        else:
            print("\n❌ Deletion cancelled.")
    
    elif choice == "4":
        print("\n👋 Exiting migration utility.")
    
    else:
        print("\n❌ Invalid choice.")


if __name__ == "__main__":
    # Initialize databases
    database.init_db()
    database_auth.init_auth_db()
    
    # Run interactive migration
    migrate_legacy_todos_interactive()
