from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import database
import notifications
from datetime import datetime

scheduler = BackgroundScheduler()

def check_and_send_reminders():
    """Check for upcoming todos and send reminders."""
    print(f"[{datetime.now()}] Checking for upcoming todos...")
    
    # Get todos due in the next 24 hours that haven't had reminders sent
    upcoming_todos = database.get_upcoming_todos(hours_ahead=24)
    
    if not upcoming_todos:
        print("No upcoming todos requiring reminders.")
        return
    
    print(f"Found {len(upcoming_todos)} todos requiring reminders.")
    
    for todo in upcoming_todos:
        print(f"Processing reminder for: {todo['title']}")
        
        email_sent = False
        sms_sent = False
        
        # Send email reminder if email is provided
        if todo.get('email'):
            email_sent = notifications.send_email_reminder(
                todo['email'],
                todo['title'],
                todo['due_date']
            )
        
        # Send SMS reminder if phone is provided
        if todo.get('phone'):
            sms_sent = notifications.send_sms_reminder(
                todo['phone'],
                todo['title'],
                todo['due_date']
            )
        
        # Mark reminder as sent if at least one notification was sent
        if email_sent or sms_sent:
            database.mark_reminder_sent(todo['id'])
            print(f"Reminder marked as sent for todo {todo['id']}")

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
