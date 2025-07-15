#!/usr/bin/env python3
"""
PyTracking Production Server Application
Handles email tracking, webhooks, and database storage for realproductpat.com
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template_string
import pytracking
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PyTracking Configuration
ENCRYPTION_KEY = os.getenv('TRACKING_ENCRYPTION_KEY', 'ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=').encode()
DOMAIN = os.getenv('DOMAIN', 'realproductpat.com')

config = pytracking.Configuration(
    base_open_tracking_url=f"https://{DOMAIN}/track/open/",
    base_click_tracking_url=f"https://{DOMAIN}/track/click/",
    webhook_url=f"https://{DOMAIN}/webhooks/tracking/",
    encryption_bytestring_key=ENCRYPTION_KEY
)

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://pytracking_user:password@localhost/pytracking_db')

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_database():
    """Initialize database tables."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Create tracking events table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tracking_events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    recipient_email VARCHAR(255),
                    sender_email VARCHAR(255),
                    case_number VARCHAR(100),
                    document_type VARCHAR(100),
                    metadata JSONB,
                    request_data JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    webhook_sent BOOLEAN DEFAULT FALSE
                );
            """)
            
            # Create indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracking_events_case_number 
                ON tracking_events(case_number);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracking_events_created_at 
                ON tracking_events(created_at);
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_tracking_events_recipient 
                ON tracking_events(recipient_email);
            """)
            
            conn.commit()
    logger.info("Database initialized successfully")

def save_tracking_event(event_type, tracking_result, request_data):
    """Save tracking event to database."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tracking_events 
                    (event_type, recipient_email, sender_email, case_number, 
                     document_type, metadata, request_data, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    event_type,
                    tracking_result.metadata.get('recipient'),
                    tracking_result.metadata.get('sender'),
                    tracking_result.metadata.get('case_number'),
                    tracking_result.metadata.get('document_type'),
                    json.dumps(tracking_result.metadata),
                    json.dumps(request_data),
                    request_data.get('user_ip'),
                    request_data.get('user_agent')
                ))
                
                event_id = cur.fetchone()['id']
                conn.commit()
                
                logger.info(f"Saved tracking event {event_id}: {event_type} for {tracking_result.metadata.get('recipient')}")
                return event_id
                
    except Exception as e:
        logger.error(f"Error saving tracking event: {e}")
        return None

@app.route('/')
def home():
    """Home page with system status."""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RealProductPat Email Tracking System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .status { padding: 20px; background: #f0f8ff; border-radius: 8px; }
            .endpoint { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🚀 RealProductPat Email Tracking System</h1>
        
        <div class="status">
            <h2>✅ System Status: Active</h2>
            <p><strong>Domain:</strong> {{ domain }}</p>
            <p><strong>Server Time:</strong> {{ timestamp }}</p>
            <p><strong>PyTracking Version:</strong> Operational</p>
        </div>
        
        <h2>📡 Tracking Endpoints</h2>
        
        <div class="endpoint">
            <h3>Open Tracking</h3>
            <code>https://{{ domain }}/track/open/&lt;encoded_data&gt;</code>
            <p>Handles email open tracking pixels</p>
        </div>
        
        <div class="endpoint">
            <h3>Click Tracking</h3>
            <code>https://{{ domain }}/track/click/&lt;encoded_data&gt;</code>
            <p>Handles email link click tracking and redirects</p>
        </div>
        
        <div class="endpoint">
            <h3>Webhook Handler</h3>
            <code>https://{{ domain }}/webhooks/tracking/</code>
            <p>Receives tracking event notifications</p>
        </div>
        
        <h2>📊 Recent Activity</h2>
        <p><a href="/admin/events">View Recent Tracking Events</a></p>
        
    </body>
    </html>
    """, domain=DOMAIN, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))

@app.route('/track/open/<path:encoded_data>')
def track_open(encoded_data):
    """Handle open tracking requests."""
    try:
        # Decode tracking data
        result = pytracking.get_open_tracking_result(
            encoded_data,
            configuration=config
        )
        
        if not result:
            logger.warning(f"Invalid tracking data: {encoded_data[:50]}...")
            return send_tracking_pixel()
        
        # Collect request data
        request_data = {
            'user_ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
            'timestamp': datetime.now().isoformat(),
            'endpoint': 'open_tracking'
        }
        
        # Save to database
        event_id = save_tracking_event('email_opened', result, request_data)
        
        # Log the event
        logger.info(f"Email opened - Case: {result.metadata.get('case_number')} "
                   f"Recipient: {result.metadata.get('recipient')} "
                   f"IP: {request_data['user_ip']}")
        
        # Send webhook notification (if configured)
        if result.webhook_url:
            try:
                pytracking.webhook.notify_webhook(config, result)
                logger.info(f"Webhook sent for event {event_id}")
            except Exception as e:
                logger.error(f"Webhook failed for event {event_id}: {e}")
        
        # Return tracking pixel
        return send_tracking_pixel()
        
    except Exception as e:
        logger.error(f"Error in open tracking: {e}")
        return send_tracking_pixel()

@app.route('/track/click/<path:encoded_data>')
def track_click(encoded_data):
    """Handle click tracking requests."""
    try:
        # Decode tracking data
        result = pytracking.get_click_tracking_result(
            encoded_data,
            configuration=config
        )
        
        if not result:
            logger.warning(f"Invalid click tracking data: {encoded_data[:50]}...")
            return redirect('https://realproductpat.com')
        
        # Collect request data
        request_data = {
            'user_ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', ''),
            'referer': request.headers.get('Referer', ''),
            'timestamp': datetime.now().isoformat(),
            'endpoint': 'click_tracking',
            'original_url': result.tracked_url
        }
        
        # Save to database
        event_id = save_tracking_event('link_clicked', result, request_data)
        
        # Log the event
        logger.info(f"Link clicked - Case: {result.metadata.get('case_number')} "
                   f"URL: {result.tracked_url} "
                   f"IP: {request_data['user_ip']}")
        
        # Send webhook notification
        if result.webhook_url:
            try:
                pytracking.webhook.notify_webhook(config, result)
                logger.info(f"Webhook sent for click event {event_id}")
            except Exception as e:
                logger.error(f"Webhook failed for click event {event_id}: {e}")
        
        # Redirect to original URL
        from flask import redirect
        return redirect(result.tracked_url)
        
    except Exception as e:
        logger.error(f"Error in click tracking: {e}")
        from flask import redirect
        return redirect('https://realproductpat.com')

@app.route('/webhooks/tracking/', methods=['POST'])
@app.route('/webhooks/legal-tracking/', methods=['POST'])
def webhook_handler():
    """Handle webhook notifications."""
    try:
        data = request.get_json()
        
        # Log webhook received
        logger.info(f"Webhook received: {data}")
        
        # You can add custom webhook processing here
        # For example, send notifications, update external systems, etc.
        
        return jsonify({'status': 'success', 'message': 'Webhook processed'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/admin/events')
def admin_events():
    """Admin page to view recent tracking events."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, event_type, recipient_email, case_number, 
                           document_type, ip_address, user_agent, created_at, metadata
                    FROM tracking_events 
                    ORDER BY created_at DESC 
                    LIMIT 50;
                """)
                events = cur.fetchall()
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tracking Events - RealProductPat</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .metadata { max-width: 300px; overflow: hidden; }
            </style>
        </head>
        <body>
            <h1>📊 Recent Tracking Events</h1>
            <p><a href="/">← Back to Home</a></p>
            
            <table>
                <tr>
                    <th>ID</th>
                    <th>Event Type</th>
                    <th>Recipient</th>
                    <th>Case Number</th>
                    <th>Document Type</th>
                    <th>IP Address</th>
                    <th>Timestamp</th>
                </tr>
                {% for event in events %}
                <tr>
                    <td>{{ event.id }}</td>
                    <td>{{ event.event_type }}</td>
                    <td>{{ event.recipient_email or 'N/A' }}</td>
                    <td>{{ event.case_number or 'N/A' }}</td>
                    <td>{{ event.document_type or 'N/A' }}</td>
                    <td>{{ event.ip_address or 'N/A' }}</td>
                    <td>{{ event.created_at.strftime('%Y-%m-%d %H:%M:%S') if event.created_at else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </table>
            
            {% if not events %}
            <p>No tracking events found.</p>
            {% endif %}
            
        </body>
        </html>
        """, events=events)
        
    except Exception as e:
        logger.error(f"Error loading events: {e}")
        return f"Error loading events: {e}", 500

def send_tracking_pixel():
    """Send the 1x1 transparent tracking pixel."""
    pixel_data, mime_type = pytracking.get_open_tracking_pixel()
    return send_file(
        io.BytesIO(pixel_data),
        mimetype=mime_type,
        as_attachment=False
    )

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1;')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'domain': DOMAIN,
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Run the application
    app.run(host='0.0.0.0', port=8000, debug=False)
