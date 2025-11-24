"""
Email Test Script - Test SMTP connection and email sending
Run this to verify email configuration is working
"""

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'abaayampics@gmail.com'
app.config['MAIL_PASSWORD'] = 'pewdqqduxaadcmrp'
app.config['MAIL_DEFAULT_SENDER'] = 'abaayampics@gmail.com'

mail = Mail(app)

def test_email_connection():
    """Test SMTP connection"""
    print("=" * 60)
    print("  EMAIL CONNECTION TEST")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Test connection
            with mail.connect() as conn:
                print("✓ SMTP connection successful!")
                print(f"  Server: {app.config['MAIL_SERVER']}")
                print(f"  Port: {app.config['MAIL_PORT']}")
                print(f"  Username: {app.config['MAIL_USERNAME']}")
                return True
        except Exception as e:
            print(f"✗ SMTP connection failed!")
            print(f"  Error: {str(e)}")
            return False

def send_test_email(recipient_email):
    """Send a test email"""
    print("\n" + "=" * 60)
    print("  SENDING TEST EMAIL")
    print("=" * 60)
    
    with app.app_context():
        try:
            msg = Message(
                subject='NeuroSight - Test Email',
                recipients=[recipient_email]
            )
            
            msg.html = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    .header { background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%); 
                             color: white; padding: 20px; border-radius: 10px; text-align: center; }
                    .content { padding: 20px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🧠 NeuroSight Test Email</h1>
                </div>
                <div class="content">
                    <h2>Email Configuration Test</h2>
                    <p>If you're reading this, your email configuration is working correctly!</p>
                    <p><strong>Server:</strong> smtp.gmail.com</p>
                    <p><strong>Port:</strong> 587</p>
                    <p><strong>TLS:</strong> Enabled</p>
                    <hr>
                    <p style="color: #10B981; font-weight: bold;">✓ Email system is operational</p>
                </div>
            </body>
            </html>
            """
            
            msg.body = """
            NeuroSight Test Email
            
            If you're reading this, your email configuration is working correctly!
            
            Server: smtp.gmail.com
            Port: 587
            TLS: Enabled
            
            ✓ Email system is operational
            """
            
            mail.send(msg)
            print(f"✓ Test email sent successfully to {recipient_email}")
            print("  Check your inbox (and spam folder)")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send test email!")
            print(f"  Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("\n🧪 NeuroSight Email System Test\n")
    
    # Test 1: SMTP Connection
    connection_ok = test_email_connection()
    
    if connection_ok:
        # Test 2: Send Email
        print("\n")
        recipient = input("Enter email address to send test email to: ").strip()
        
        if recipient:
            send_test_email(recipient)
        else:
            print("\n⚠️  No email address provided, skipping email send test")
    else:
        print("\n❌ Cannot send test email - connection failed")
        print("\nPossible issues:")
        print("  1. Gmail App Password might be incorrect")
        print("  2. 2-Factor Authentication not enabled on Gmail")
        print("  3. 'Less secure app access' might be disabled")
        print("  4. Internet connection issue")
        print("  5. Gmail account might be blocked")
    
    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)
