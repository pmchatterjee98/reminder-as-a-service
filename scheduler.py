from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import database
import database_auth
import database_multi_user
import notifications
from datetime import datetime

scheduler = BackgroundScheduler()

def check_and_send_reminders():
    """Check for upcoming todos and send reminders for all users (automatically sends for tasks <= 24 hours)."""
    print(f"[{datetime.now()}] Checking for upcoming todos across all users...")
    
    # Get all users
    all_users = database_auth.get_all_users()
    
    if not all_users:
        print("No users found in the system.")
        return
    
    total_reminders = 0
    
    # Process reminders for each user
    for user in all_users:
        # Use internal RAAS user ID (not auth_provider_id) since that's what's stored in todos.user_id
        user_id = user['id']
        
        # Get upcoming todos for this user (tasks with <= 24 hours remaining)
        upcoming_todos = database_multi_user.get_upcoming_todos_for_user(user_id)
        
        if not upcoming_todos:
            continue
        
        print(f"User {user_id}: Found {len(upcoming_todos)} todos requiring reminders.")
        total_reminders += len(upcoming_todos)
        
        for todo in upcoming_todos:
            print(f"  Processing reminder for: {todo['title']}")
            
            # Check quiet hours ONCE before any sends to avoid race conditions
            in_quiet_hours = notifications.is_quiet_hours()
            
            email_sent = False
            sms_sent = False
            whatsapp_sent = False
            sms_blocked_by_quiet_hours = False
            whatsapp_blocked_by_quiet_hours = False
            
            # Send email reminder if email is provided in the todo
            # Email is not affected by quiet hours
            if todo.get('email'):
                email_sent = notifications.send_email_reminder(
                    todo['email'],
                    todo['title'],
                    todo['due_date']
                )
            
            # Send SMS reminder if phone is provided in the todo
            if todo.get('phone'):
                if in_quiet_hours:
                    # Skip SMS during quiet hours - will retry on next hourly check
                    sms_blocked_by_quiet_hours = True
                    print(f"  SMS blocked by quiet hours (12am-9:30am) - will retry after 9:30am")
                else:
                    sms_sent = notifications.send_sms_reminder(
                        todo['phone'],
                        todo['title'],
                        todo['due_date']
                    )
            
            # Send WhatsApp reminder if whatsapp_phone is provided in the todo
            if todo.get('whatsapp_phone'):
                if in_quiet_hours:
                    # Skip WhatsApp during quiet hours - will retry on next hourly check
                    whatsapp_blocked_by_quiet_hours = True
                    print(f"  WhatsApp blocked by quiet hours (12am-9:30am) - will retry after 9:30am")
                else:
                    whatsapp_sent = notifications.send_whatsapp_reminder(
                        todo['whatsapp_phone'],
                        todo['title'],
                        todo['due_date']
                    )
            
            # Determine if reminder should be marked as sent
            should_mark_sent = False
            
            if email_sent or sms_sent or whatsapp_sent:
                # At least one channel succeeded
                if sms_blocked_by_quiet_hours or whatsapp_blocked_by_quiet_hours:
                    # If email succeeded but SMS/WhatsApp blocked, mark as sent to avoid duplicate emails
                    # Note: SMS/WhatsApp will not be sent for this reminder (limitation of quiet hours)
                    if email_sent:
                        should_mark_sent = True
                        if sms_blocked_by_quiet_hours:
                            print(f"  ⚠️  SMS blocked by quiet hours - will not be sent for this reminder")
                        if whatsapp_blocked_by_quiet_hours:
                            print(f"  ⚠️  WhatsApp blocked by quiet hours - will not be sent for this reminder")
                    else:
                        # Pure SMS/WhatsApp reminder - don't mark as sent, will retry after quiet hours
                        print(f"  Reminder NOT marked as sent - will retry after quiet hours")
                else:
                    # No channels blocked by quiet hours
                    should_mark_sent = True
            
            if should_mark_sent:
                database.mark_reminder_sent(todo['id'])
                print(f"  Reminder marked as sent for todo {todo['id']}")
    
    if total_reminders == 0:
        print("No upcoming todos requiring reminders across all users.")
    else:
        print(f"Processed {total_reminders} total reminders.")

def start_scheduler():
    """Start the background scheduler to check for reminders every hour."""
    if not scheduler.running:
        # Check for reminders every hour
        scheduler.add_job(
            check_and_send_reminders,
            trigger=IntervalTrigger(hours=1),
            id='reminder_checker',
            replace_existing=True
        )
        scheduler.start()
        print("Reminder scheduler started. Checking every hour.")
        
        # Run immediately on startup
        check_and_send_reminders()

def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("Reminder scheduler stopped.")
