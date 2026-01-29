#!/usr/bin/env python3
"""
Email Spammer Script

Sends the content of message.txt to all email addresses in emails.json using Gmail SMTP
Requires Gmail account credentials and an app password

Usage:
    python3 spammer.py --email YOUR_EMAIL@gmail.com --password YOUR_APP_PASSWORD
    python3 spammer.py --email YOUR_EMAIL@gmail.com --password YOUR_APP_PASSWORD --subject "Custom Subject"
"""

import json
import smtplib
import argparse
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP settings
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


def load_emails(filepath):
    """Load email addresses from JSON file"""
    try:
        with open(filepath, 'r') as f:
            emails = json.load(f)
            if not isinstance(emails, list):
                print(f"Error: {filepath} must contain a JSON array of emails")
                return []
            return [e for e in emails if isinstance(e, str) and '@' in e]
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filepath}")
        return []


def load_message(filepath):
    """Load message content from text file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return None


def send_emails(sender_email, sender_password, recipient_emails, subject, message_body):
    """Send emails to all recipients using Gmail SMTP"""
    
    try:
        # Connect to Gmail SMTP server
        print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        
        # Login
        print(f"Logging in as {sender_email}...")
        server.login(sender_email, sender_password)
        
        success_count = 0
        fail_count = 0
        
        # Send to each recipient
        for recipient in recipient_emails:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(message_body, 'plain'))
                
                # Send
                server.send_message(msg)
                print(f"✓ Sent to {recipient}")
                success_count += 1
                
            except Exception as e:
                print(f"✗ Failed to send to {recipient}: {e}")
                fail_count += 1
        
        # Close connection
        server.quit()
        
        print(f"\n--- Summary ---")
        print(f"Total: {len(recipient_emails)} | Success: {success_count} | Failed: {fail_count}")
        
        return success_count, fail_count
        
    except smtplib.SMTPAuthenticationError:
        print("Error: Authentication failed. Check your email and password.")
        print("Note: Use Gmail App Password, not your regular password.")
        print("Generate one at: https://myaccount.google.com/apppasswords")
        return 0, len(recipient_emails)
    except Exception as e:
        print(f"Error: {e}")
        return 0, len(recipient_emails)


def main():
    parser = argparse.ArgumentParser(
        description='Send emails to a list of recipients using Gmail SMTP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 spammer.py --email myemail@gmail.com --password myapppassword
  python3 spammer.py --email myemail@gmail.com --password myapppassword --subject "Hello"
  python3 spammer.py --email myemail@gmail.com --password myapppassword --emails filtered_emails.json

Note: You must use a Gmail App Password, not your regular Gmail password.
Generate one at: https://myaccount.google.com/apppasswords
        """
    )
    
    parser.add_argument('--email', required=True, help='Your Gmail address')
    parser.add_argument('--password', required=True, help='Your Gmail App Password')
    parser.add_argument('--subject', default="You've Won! Claim Your Prize NOW", help='Email subject line')
    parser.add_argument('--emails', default='emails.json', help='Path to JSON file with recipient emails (default: emails.json)')
    parser.add_argument('--message', default='message.txt', help='Path to message text file (default: ../message.txt)')
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    emails_path = os.path.join(script_dir, args.emails)
    message_path = os.path.join(script_dir, args.message)
    
    # Load recipient emails
    print(f"Loading recipients from {emails_path}...")
    recipients = load_emails(emails_path)
    if not recipients:
        print("No valid recipients found. Exiting.")
        sys.exit(1)
    
    print(f"Found {len(recipients)} recipients")
    
    # Load message content
    print(f"Loading message from {message_path}...")
    message = load_message(message_path)
    if not message:
        print("No message content found. Exiting.")
        sys.exit(1)
    
    print(f"Message loaded ({len(message)} characters)")
    
    # Confirm before sending
    print(f"\n--- Ready to send ---")
    print(f"From: {args.email}")
    print(f"To: {len(recipients)} recipients")
    print(f"Subject: {args.subject}")
    print(f"\nMessage preview:")
    print("-" * 50)
    print(message[:200] + ("..." if len(message) > 200 else ""))
    print("-" * 50)
    
    confirm = input("\nProceed with sending? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Cancelled.")
        sys.exit(0)
    
    # Send emails
    print("\nSending emails...\n")
    send_emails(args.email, args.password, recipients, args.subject, message)


if __name__ == '__main__':
    main()
