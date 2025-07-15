#!/usr/bin/env python3
"""
Quick Start Email Tracking Setup
================================

This is a minimal setup to get you started with email tracking using your domain.
Run this script to start the tracking server and see example emails.

Usage:
1. python quick_start_tracking.py          # See example
2. python quick_start_tracking.py --server # Start tracking server
"""

from flask import Flask, request, Response, jsonify
import pytracking
import sqlite3
import json
from datetime import datetime
from cryptography.fernet import Fernet

# ============================================================================
# SIMPLE DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize simple SQLite database."""
    conn = sqlite3.connect('email_tracking.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def save_open_event(user_id, campaign_id, email_address, ip_address, user_agent, metadata):
    """Save email open to database."""
    conn = sqlite3.connect('email_tracking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO email_opens 
        (user_id, campaign_id, email_address, ip_address, user_agent, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, campaign_id, email_address, ip_address, user_agent, json.dumps(metadata)))
    
    conn.commit()
    conn.close()
    print(f"📊 Saved: {email_address} opened email from campaign {campaign_id}")

# ============================================================================
# TRACKING CONFIGURATION
# ============================================================================

# Generate encryption key (in production, store this securely!)
ENCRYPTION_KEY = Fernet.generate_key()

# Configure PyTracking for your domain
config = pytracking.Configuration(
    base_open_tracking_url="https://realproductpat.com/track/open/",
    base_click_tracking_url="https://realproductpat.com/track/click/",
    webhook_url="https://realproductpat.com/webhooks/tracking/",
    encryption_bytestring_key=ENCRYPTION_KEY
)

print(f"🔑 Encryption key: {ENCRYPTION_KEY.decode()}")
print("💡 Save this key securely for production use!")

# ============================================================================
# FLASK WEBHOOK SERVER
# ============================================================================

app = Flask(__name__)

@app.route('/track/open/<path:encoded_data>')
def track_open(encoded_data):
    """Handle email open tracking."""
    try:
        # Decode the tracking data
        result = pytracking.get_open_tracking_result(
            encoded_data,
            configuration=config
        )
        
        if result and result.metadata:
            # Get client info
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            # Save to database
            save_open_event(
                user_id=result.metadata.get('user_id'),
                campaign_id=result.metadata.get('campaign_id'),
                email_address=result.metadata.get('email_address'),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=result.metadata
            )
            
            print(f"✅ Email opened by {result.metadata.get('email_address')}")
        
        # Return the tracking pixel
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)
        
    except Exception as e:
        print(f"❌ Tracking error: {e}")
        # Always return pixel, even on error
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)

@app.route('/webhooks/tracking/', methods=['POST'])
def webhook():
    """Handle webhook notifications."""
    try:
        data = request.get_json()
        print(f"📞 Webhook received: {data}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/stats')
def stats():
    """Show tracking statistics."""
    conn = sqlite3.connect('email_tracking.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM email_opens')
    total_opens = cursor.fetchone()[0]
    
    cursor.execute('SELECT campaign_id, COUNT(*) FROM email_opens GROUP BY campaign_id')
    campaign_stats = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        "total_opens": total_opens,
        "campaigns": [{"campaign_id": c[0], "opens": c[1]} for c in campaign_stats]
    })

@app.route('/')
def home():
    """Home page with status."""
    return jsonify({
        "status": "RealProductPat Email Tracking Server",
        "endpoints": {
            "tracking": "/track/open/<encoded_data>",
            "webhook": "/webhooks/tracking/",
            "stats": "/stats"
        }
    })

# ============================================================================
# EMAIL CREATION FUNCTIONS
# ============================================================================

def create_tracked_email(recipient_email, campaign_id="demo", user_id=None):
    """Create an email with tracking pixel for your domain."""
    
    if not user_id:
        user_id = recipient_email.split('@')[0]
    
    # Metadata to track
    metadata = {
        "user_id": user_id,
        "campaign_id": campaign_id,
        "email_address": recipient_email,
        "timestamp": datetime.now().isoformat()
    }
    
    # Generate tracking pixel URL
    tracking_url = pytracking.get_open_tracking_url(
        configuration=config,
        metadata=metadata
    )
    
    # Create HTML email
    html_email = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to RealProductPat!</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h1>🎉 Welcome to RealProductPat!</h1>
            <p style="font-size: 18px; margin: 0;">Your journey starts here</p>
        </div>
        
        <div style="padding: 30px 20px;">
            <h2>Hi {user_id}! 👋</h2>
            
            <p style="font-size: 16px; line-height: 1.6; color: #333;">
                We're thrilled to have you join the RealProductPat community! 
                Here's what you can expect:
            </p>
            
            <ul style="font-size: 16px; line-height: 1.8; color: #333;">
                <li>🚀 <strong>Product Updates</strong> - Be the first to know about new features</li>
                <li>💡 <strong>Tips & Tricks</strong> - Get the most out of our platform</li>
                <li>🎯 <strong>Exclusive Content</strong> - Access to member-only resources</li>
                <li>🤝 <strong>Community</strong> - Connect with like-minded users</li>
            </ul>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="https://realproductpat.com/dashboard" 
                   style="background: #667eea; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    🏁 Get Started Now
                </a>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 30px 0;">
                <h3 style="margin-top: 0; color: #495057;">📧 Email Tracking Demo</h3>
                <p style="margin-bottom: 0; color: #6c757d; font-size: 14px;">
                    This email includes a tracking pixel to demonstrate PyTracking functionality.
                    Campaign ID: <strong>{campaign_id}</strong>
                </p>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                Questions? Just reply to this email - we'd love to hear from you!
            </p>
        </div>
        
        <div style="border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #999; font-size: 12px;">
            <p>This email was sent to {recipient_email}</p>
            <p>RealProductPat • San Francisco, CA • USA</p>
        </div>
        
        <!-- 👁️ TRACKING PIXEL (invisible) -->
        <img src="{tracking_url}" width="1" height="1" style="display:none;" alt="">
        
    </body>
    </html>
    """
    
    return html_email, tracking_url, metadata

# ============================================================================
# MAIN DEMO
# ============================================================================

def demo():
    """Run demo showing email creation and tracking setup."""
    
    print("🚀 RealProductPat Email Tracking Demo")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Create sample emails
    recipients = [
        "alice@example.com",
        "bob@example.com", 
        "charlie@example.com"
    ]
    
    print("\n📧 Creating tracked emails...")
    
    for recipient in recipients:
        html_content, tracking_url, metadata = create_tracked_email(
            recipient_email=recipient,
            campaign_id="welcome_2023",
            user_id=recipient.split('@')[0]
        )
        
        print(f"\n✅ Email created for: {recipient}")
        print(f"🔗 Tracking URL: {tracking_url}")
        print(f"📊 Metadata: {metadata}")
        
        # Save the HTML to a file so you can see it
        filename = f"email_{recipient.split('@')[0]}.html"
        with open(filename, 'w') as f:
            f.write(html_content)
        print(f"💾 Saved HTML to: {filename}")
    
    print(f"\n🎯 Your tracking configuration:")
    print(f"   Domain: realproductpat.com")
    print(f"   Open tracking: {config.base_open_tracking_url}")
    print(f"   Click tracking: {config.base_click_tracking_url}")
    print(f"   Webhook: {config.webhook_url}")
    print(f"   Encryption: {'✅ Enabled' if config.encryption_key else '❌ Disabled'}")
    
    print(f"\n🌐 To start the webhook server:")
    print(f"   python {__file__} --server")
    print(f"\n📊 Then visit: http://localhost:5000/stats")

if __name__ == "__main__":
    import sys
    
    if "--server" in sys.argv:
        print("🌐 Starting RealProductPat tracking server...")
        print("📡 Endpoints:")
        print("   http://localhost:5000/")
        print("   http://localhost:5000/track/open/<data>")
        print("   http://localhost:5000/webhooks/tracking/")
        print("   http://localhost:5000/stats")
        print("\n🔑 Press Ctrl+C to stop")
        
        init_db()  # Initialize database
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        demo()
