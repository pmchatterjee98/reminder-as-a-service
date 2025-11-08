"""
Test script for RAAS email and SMS notifications
"""

import notifications
from datetime import datetime, timedelta

def test_notifications():
    """Test both email and SMS notifications"""
    
    # Test data
    test_title = "Test RAAS Notification"
    test_due_date = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 60)
    print("⚡ RAAS Notification Test")
    print("=" * 60)
    print()
    
    # Get test contact info
    print("Please provide test contact information:")
    print()
    
    # Test email
    test_email = input("Enter email address to test (or press Enter to skip): ").strip()
    if test_email:
        print(f"\n📧 Testing email notification to: {test_email}")
        email_result = notifications.send_email_reminder(test_email, test_title, test_due_date)
        if email_result:
            print("✅ Email sent successfully!")
        else:
            print("❌ Email failed to send. Check the logs above for details.")
    else:
        print("⏭️  Skipping email test")
    
    print()
    
    # Test SMS
    test_phone = input("Enter phone number to test (format: +1234567890, or press Enter to skip): ").strip()
    if test_phone:
        print(f"\n📱 Testing SMS notification to: {test_phone}")
        sms_result = notifications.send_sms_reminder(test_phone, test_title, test_due_date)
        if sms_result:
            print("✅ SMS sent successfully!")
        else:
            print("❌ SMS failed to send. Check the logs above for details.")
    else:
        print("⏭️  Skipping SMS test")
    
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_notifications()
