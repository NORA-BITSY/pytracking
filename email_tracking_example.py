#!/usr/bin/env python3
"""
Complete Email Tracking System Example
=====================================

This example shows how to:
1. Send emails with open tracking pixels
2. Set up webhook handlers to receive tracking events
3. Store tracking data in a database
4. Use your domain: realproductpat.com

Requirements:
- pip install 'pytracking[all]'
- pip install flask sqlalchemy requests
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, Response, jsonify
from cryptography.fernet import Fernet
import pytracking
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# ============================================================================
# 1. DATABASE SETUP
# ============================================================================

class TrackingDatabase:
    def __init__(self, db_path="tracking.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with tracking tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create email campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create email opens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_opens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                campaign_id TEXT,
                email_address TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Create email clicks table (for future use)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                campaign_id TEXT,
                email_address TEXT,
                original_url TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def save_email_open(self, user_id, campaign_id, email_address, ip_address, user_agent, metadata):
        """Save email open event to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_opens 
            (user_id, campaign_id, email_address, ip_address, user_agent, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, campaign_id, email_address, ip_address, user_agent, json.dumps(metadata)))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved email open: user_id={user_id}, campaign_id={campaign_id}")
    
    def get_campaign_stats(self, campaign_id):
        """Get statistics for a campaign."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM email_opens WHERE campaign_id = ?', (campaign_id,))
        opens = cursor.fetchone()[0]
        
        conn.close()
        return {"campaign_id": campaign_id, "total_opens": opens}

# ============================================================================
# 2. PYTRACKING CONFIGURATION
# ============================================================================

class EmailTrackingService:
    def __init__(self):
        # Generate or load encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        
        # Configure PyTracking
        self.config = pytracking.Configuration(
            base_open_tracking_url="https://realproductpat.com/track/open/",
            base_click_tracking_url="https://realproductpat.com/track/click/",
            webhook_url="https://realproductpat.com/webhooks/tracking/",
            encryption_bytestring_key=self.encryption_key,
            default_metadata={"source": "email_campaign"}
        )
        
        self.db = TrackingDatabase()
        print("✅ Email tracking service initialized")
    
    def _get_or_create_encryption_key(self):
        """Get encryption key from environment or create new one."""
        key = os.environ.get('PYTRACKING_ENCRYPTION_KEY')
        if key:
            return key.encode()
        else:
            # Generate new key for development
            new_key = Fernet.generate_key()
            print(f"🔑 Generated new encryption key: {new_key.decode()}")
            print("💡 Set PYTRACKING_ENCRYPTION_KEY environment variable to persist this key")
            return new_key
    
    def create_tracked_email(self, recipient_email, subject, campaign_id="default", user_id=None):
        """Create an email with tracking pixel."""
        
        # Generate user_id if not provided
        if not user_id:
            user_id = recipient_email.split('@')[0]  # Use email prefix as user_id
        
        # Metadata for tracking
        metadata = {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "email_address": recipient_email,
            "subject": subject
        }
        
        # Generate tracking pixel URL
        tracking_pixel_url = pytracking.get_open_tracking_url(
            configuration=self.config,
            metadata=metadata
        )
        
        # Create HTML email with tracking pixel
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{subject}</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h1 style="color: #333; text-align: center;">Welcome to RealProductPat!</h1>
                
                <p style="color: #666; font-size: 16px; line-height: 1.6;">
                    Hi there! 👋
                </p>
                
                <p style="color: #666; font-size: 16px; line-height: 1.6;">
                    Thank you for joining our community. We're excited to have you on board!
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://realproductpat.com/welcome" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Get Started
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px; line-height: 1.6;">
                    If you have any questions, feel free to reply to this email.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    This email was sent to {recipient_email}<br>
                    RealProductPat • San Francisco, CA
                </p>
            </div>
            
            <!-- Tracking pixel (invisible) -->
            <img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" alt="" />
        </body>
        </html>
        """
        
        return html_content, tracking_pixel_url, metadata
    
    def send_email_smtp(self, recipient_email, subject, html_content, 
                       smtp_server="smtp.gmail.com", smtp_port=587, 
                       sender_email=None, sender_password=None):
        """Send email using SMTP (Gmail example)."""
        
        if not sender_email or not sender_password:
            print("⚠️  SMTP credentials not provided. Email not sent.")
            print("📧 HTML content generated (see below):")
            print("-" * 50)
            print(html_content)
            print("-" * 50)
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

# ============================================================================
# 3. WEBHOOK HANDLER (Flask Web Server)
# ============================================================================

app = Flask(__name__)
tracking_service = EmailTrackingService()

@app.route('/track/open/<path:encoded_data>')
def handle_open_tracking(encoded_data):
    """Handle open tracking requests and return tracking pixel."""
    
    try:
        # Decode tracking data
        result = pytracking.get_open_tracking_result(
            encoded_data,
            configuration=tracking_service.config
        )
        
        if result and result.metadata:
            # Extract client information
            user_agent = request.headers.get('User-Agent', '')
            ip_address = request.remote_addr
            
            # Save to database
            tracking_service.db.save_email_open(
                user_id=result.metadata.get('user_id'),
                campaign_id=result.metadata.get('campaign_id'),
                email_address=result.metadata.get('email_address'),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=result.metadata
            )
            
            print(f"📊 Email opened by {result.metadata.get('email_address')}")
            
        # Return tracking pixel
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)
        
    except Exception as e:
        print(f"❌ Error handling open tracking: {e}")
        # Return tracking pixel anyway
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)

@app.route('/webhooks/tracking/', methods=['POST'])
def webhook_handler():
    """Handle webhook notifications from tracking events."""
    
    try:
        data = request.get_json()
        print(f"📞 Webhook received: {data}")
        
        # Process webhook data (implement your logic here)
        # This could trigger additional actions like:
        # - Send to analytics service
        # - Update user engagement scores
        # - Trigger follow-up emails
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/stats/<campaign_id>')
def get_campaign_stats(campaign_id):
    """Get campaign statistics."""
    stats = tracking_service.db.get_campaign_stats(campaign_id)
    return jsonify(stats)

@app.route('/')
def index():
    """Basic status page."""
    return jsonify({
        "status": "Email tracking system running",
        "endpoints": {
            "tracking": "/track/open/<encoded_data>",
            "webhook": "/webhooks/tracking/",
            "stats": "/stats/<campaign_id>"
        }
    })

# ============================================================================
# 4. EXAMPLE USAGE
# ============================================================================

def main():
    """Example of how to use the email tracking system."""
    
    print("🚀 Email Tracking System Demo")
    print("=" * 50)
    
    # Initialize tracking service
    service = EmailTrackingService()
    
    # Example: Create and send tracked email
    recipient = "user@example.com"
    subject = "Welcome to RealProductPat!"
    campaign_id = "welcome_series_2023"
    
    # Create tracked email
    html_content, tracking_url, metadata = service.create_tracked_email(
        recipient_email=recipient,
        subject=subject,
        campaign_id=campaign_id,
        user_id="demo_user_123"
    )
    
    print(f"📧 Created tracked email for: {recipient}")
    print(f"🔗 Tracking URL: {tracking_url}")
    print(f"📊 Metadata: {metadata}")
    
    # Send email (requires SMTP credentials)
    # Uncomment and fill in your SMTP details:
    """
    service.send_email_smtp(
        recipient_email=recipient,
        subject=subject,
        html_content=html_content,
        sender_email="your-email@gmail.com",
        sender_password="your-app-password"
    )
    """
    
    print("\n💡 To send emails, uncomment the SMTP section and add your credentials")
    print("\n🌐 To start the webhook server, run:")
    print("   python email_tracking_example.py --server")

if __name__ == "__main__":
    import sys
    
    if "--server" in sys.argv:
        print("🌐 Starting Flask webhook server...")
        print("📡 Open tracking endpoint: http://localhost:5000/track/open/")
        print("🪝 Webhook endpoint: http://localhost:5000/webhooks/tracking/")
        print("📊 Stats endpoint: http://localhost:5000/stats/campaign_id")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        main()
