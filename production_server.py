#!/usr/bin/env python3
"""
Production Flask Server for PyTracking Email Tracking
====================================================

This is a production-ready Flask server that you can deploy to your server
to handle email tracking for realproductpat.com

Features:
- Email open tracking
- Click tracking  
- Webhook handling
- Database storage
- Security headers
- Error handling
- Logging

Deployment Instructions:
1. Copy this file to your server
2. Install dependencies: pip install 'pytracking[all]' flask gunicorn
3. Set environment variables
4. Run with: gunicorn -w 4 -b 0.0.0.0:5000 production_server:app
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from flask import Flask, request, Response, jsonify, render_template_string
from cryptography.fernet import Fernet
import pytracking
import pytracking.webhook

# ============================================================================
# CONFIGURATION
# ============================================================================

# Environment variables (set these on your server)
ENCRYPTION_KEY = os.environ.get('PYTRACKING_ENCRYPTION_KEY', Fernet.generate_key())
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

DATABASE_PATH = os.environ.get('PYTRACKING_DB_PATH', '/var/lib/pytracking/tracking.db')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret-key')
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', 'realproductpat.com').split(',')

# PyTracking Configuration
config = pytracking.Configuration(
    base_open_tracking_url="https://realproductpat.com/track/open/",
    base_click_tracking_url="https://realproductpat.com/track/click/",
    webhook_url="https://realproductpat.com/webhooks/tracking/",
    encryption_bytestring_key=ENCRYPTION_KEY
)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/pytracking.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def init_database():
    """Initialize the tracking database."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Email opens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_opens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT UNIQUE,
            recipient_email TEXT,
            sender_email TEXT,
            campaign_id TEXT,
            document_type TEXT,
            case_number TEXT,
            ip_address TEXT,
            user_agent TEXT,
            country TEXT,
            city TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            raw_request TEXT
        )
    ''')
    
    # Email clicks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_id TEXT,
            recipient_email TEXT,
            original_url TEXT,
            campaign_id TEXT,
            link_type TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    # Webhook logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webhook_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            payload TEXT,
            response_status INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_email_open(tracking_result, request_info):
    """Save email open event to database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO email_opens 
            (tracking_id, recipient_email, sender_email, campaign_id, document_type, 
             case_number, ip_address, user_agent, timestamp, metadata, raw_request)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tracking_result.metadata.get('document_id', 'unknown'),
            tracking_result.metadata.get('recipient'),
            tracking_result.metadata.get('sender'),
            tracking_result.metadata.get('campaign_id'),
            tracking_result.metadata.get('document_type'),
            tracking_result.metadata.get('case_number'),
            request_info.get('ip_address'),
            request_info.get('user_agent'),
            datetime.now(),
            json.dumps(tracking_result.metadata),
            json.dumps(request_info)
        ))
        
        conn.commit()
        logger.info(f"Saved email open: {tracking_result.metadata.get('document_id')}")
        
    except Exception as e:
        logger.error(f"Error saving email open: {e}")
    finally:
        conn.close()

def get_tracking_stats(campaign_id=None, days=30):
    """Get tracking statistics."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    where_clause = "WHERE timestamp >= datetime('now', '-{} days')".format(days)
    if campaign_id:
        where_clause += f" AND campaign_id = '{campaign_id}'"
    
    # Email opens
    cursor.execute(f'''
        SELECT COUNT(*) as total_opens,
               COUNT(DISTINCT recipient_email) as unique_opens,
               COUNT(DISTINCT ip_address) as unique_ips
        FROM email_opens {where_clause}
    ''')
    
    open_stats = cursor.fetchone()
    
    # Recent opens
    cursor.execute(f'''
        SELECT recipient_email, timestamp, document_type, case_number
        FROM email_opens {where_clause}
        ORDER BY timestamp DESC LIMIT 10
    ''')
    
    recent_opens = cursor.fetchall()
    
    conn.close()
    
    return {
        'total_opens': open_stats[0],
        'unique_opens': open_stats[1], 
        'unique_ips': open_stats[2],
        'recent_opens': recent_opens
    }

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = WEBHOOK_SECRET

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ============================================================================
# TRACKING ENDPOINTS
# ============================================================================

@app.route('/track/open/<path:encoded_data>')
def handle_open_tracking(encoded_data):
    """Handle email open tracking requests."""
    try:
        # Get request information
        request_info = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
            'timestamp': datetime.now().isoformat(),
            'headers': dict(request.headers)
        }
        
        # Decode tracking data
        tracking_result = pytracking.get_open_tracking_result(
            encoded_data,
            configuration=config,
            request_data=request_info
        )
        
        if tracking_result:
            logger.info(f"Email opened: {tracking_result.metadata.get('document_id', 'unknown')}")
            
            # Save to database
            save_email_open(tracking_result, request_info)
            
            # Send webhook if configured
            if tracking_result.webhook_url:
                try:
                    response = pytracking.webhook.send_webhook(tracking_result, config)
                    logger.info(f"Webhook sent: {response.status_code}")
                except Exception as e:
                    logger.error(f"Webhook failed: {e}")
            
            # Return tracking pixel
            pixel_data, mime_type = pytracking.get_open_tracking_pixel()
            return Response(
                pixel_data,
                mimetype=mime_type,
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
        else:
            logger.warning(f"Invalid tracking data: {encoded_data[:50]}...")
            return Response(status=404)
            
    except Exception as e:
        logger.error(f"Tracking error: {e}")
        # Still return a pixel to avoid broken images
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)

@app.route('/track/click/<path:encoded_data>')
def handle_click_tracking(encoded_data):
    """Handle email click tracking requests."""
    try:
        # Get request information
        request_info = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # Decode tracking data
        tracking_result = pytracking.get_click_tracking_result(
            encoded_data,
            configuration=config,
            request_data=request_info
        )
        
        if tracking_result and tracking_result.tracked_url:
            logger.info(f"Link clicked: {tracking_result.tracked_url}")
            
            # Save to database (you can implement this similar to email opens)
            # save_email_click(tracking_result, request_info)
            
            # Send webhook if configured
            if tracking_result.webhook_url:
                try:
                    response = pytracking.webhook.send_webhook(tracking_result, config)
                    logger.info(f"Click webhook sent: {response.status_code}")
                except Exception as e:
                    logger.error(f"Click webhook failed: {e}")
            
            # Redirect to original URL
            return Response(
                status=302,
                headers={'Location': tracking_result.tracked_url}
            )
        else:
            logger.warning(f"Invalid click tracking data: {encoded_data[:50]}...")
            return Response(status=404)
            
    except Exception as e:
        logger.error(f"Click tracking error: {e}")
        return Response(status=404)

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.route('/webhooks/tracking/', methods=['POST'])
def webhook_handler():
    """Handle incoming webhook notifications."""
    try:
        payload = request.get_json()
        
        logger.info(f"Webhook received: {payload.get('metadata', {}).get('document_type', 'unknown')}")
        
        # Log webhook to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO webhook_logs (event_type, payload, response_status)
            VALUES (?, ?, ?)
        ''', (
            'tracking_event',
            json.dumps(payload),
            200
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Webhook processed'})
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================================
# ADMIN/STATS ENDPOINTS
# ============================================================================

@app.route('/admin/stats')
def admin_stats():
    """Show tracking statistics (protect this endpoint in production!)."""
    try:
        # Get query parameters
        campaign_id = request.args.get('campaign_id')
        days = int(request.args.get('days', 30))
        
        stats = get_tracking_stats(campaign_id, days)
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyTracking Stats - RealProductPat</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .stat { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 5px; }
                .recent { background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>📊 Email Tracking Statistics</h1>
            <p>Domain: <strong>realproductpat.com</strong> | Last {{ days }} days</p>
            
            <div class="stat">
                <h3>📈 Summary Stats</h3>
                <p><strong>Total Opens:</strong> {{ stats.total_opens }}</p>
                <p><strong>Unique Recipients:</strong> {{ stats.unique_opens }}</p>
                <p><strong>Unique IP Addresses:</strong> {{ stats.unique_ips }}</p>
            </div>
            
            <div class="recent">
                <h3>🕒 Recent Opens</h3>
                <table>
                    <tr>
                        <th>Recipient</th>
                        <th>Timestamp</th>
                        <th>Document Type</th>
                        <th>Case Number</th>
                    </tr>
                    {% for open in stats.recent_opens %}
                    <tr>
                        <td>{{ open[0] or 'N/A' }}</td>
                        <td>{{ open[1] }}</td>
                        <td>{{ open[2] or 'N/A' }}</td>
                        <td>{{ open[3] or 'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            
            <div class="stat">
                <h3>🔧 Configuration</h3>
                <p><strong>Encryption:</strong> ✅ Enabled</p>
                <p><strong>Database:</strong> {{ db_path }}</p>
                <p><strong>Webhook URL:</strong> {{ webhook_url }}</p>
            </div>
        </body>
        </html>
        """
        
        from jinja2 import Template
        template = Template(html_template)
        
        return template.render(
            stats=stats,
            days=days,
            db_path=DATABASE_PATH,
            webhook_url=config.webhook_url
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'pytracking-server',
        'domain': 'realproductpat.com'
    })

@app.route('/')
def index():
    """Root endpoint."""
    return jsonify({
        'service': 'PyTracking Email Tracking Server',
        'domain': 'realproductpat.com',
        'endpoints': {
            'open_tracking': '/track/open/<encoded_data>',
            'click_tracking': '/track/click/<encoded_data>',
            'webhook': '/webhooks/tracking/',
            'stats': '/admin/stats',
            'health': '/health'
        }
    })

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Print configuration info
    logger.info("=" * 60)
    logger.info("🚀 PyTracking Server Starting")
    logger.info(f"📧 Domain: realproductpat.com")
    logger.info(f"🔐 Encryption: {'✅ Enabled' if ENCRYPTION_KEY else '❌ Disabled'}")
    logger.info(f"💾 Database: {DATABASE_PATH}")
    logger.info(f"📊 Stats: /admin/stats")
    logger.info("=" * 60)
    
    # Development server (use gunicorn for production)
    app.run(host='0.0.0.0', port=5000, debug=False)
