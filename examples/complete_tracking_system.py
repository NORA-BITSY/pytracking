#!/usr/bin/env python3
"""
Complete Email Tracking System Example
=====================================

This example demonstrates a complete email tracking implementation with:
- Database storage
- Web UI dashboard
- REST API
- Email integration
- Analytics and reporting

Requirements:
pip install pytracking[all] flask sqlalchemy flask-sqlalchemy requests matplotlib plotly
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytracking
from cryptography.fernet import Fernet
from flask import Flask, request, redirect, Response, render_template, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
import requests

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Generate encryption key (store securely in production)
ENCRYPTION_KEY = Fernet.generate_key()

# PyTracking Configuration
TRACKING_CONFIG = pytracking.Configuration(
    base_open_tracking_url="http://localhost:5000/track/open/",
    base_click_tracking_url="http://localhost:5000/track/click/",
    webhook_url="http://localhost:5000/webhook/tracking",
    encryption_bytestring_key=ENCRYPTION_KEY,
    default_metadata={"app": "email_tracker", "version": "1.0"}
)

# Database Models
class Campaign(db.Model):
    """Email campaign model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_count = db.Column(db.Integer, default=0)
    
    # Relationships
    emails = db.relationship('Email', backref='campaign', lazy=True)
    events = db.relationship('TrackingEvent', backref='campaign', lazy=True)

    def __repr__(self):
        return f'<Campaign {self.name}>'

class Email(db.Model):
    """Individual email model"""
    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(120), nullable=False)
    recipient_name = db.Column(db.String(100))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tracking status
    opened = db.Column(db.Boolean, default=False)
    first_opened_at = db.Column(db.DateTime)
    clicks = db.Column(db.Integer, default=0)
    
    # Relationships
    events = db.relationship('TrackingEvent', backref='email', lazy=True)

    def __repr__(self):
        return f'<Email {self.recipient_email}>'

class TrackingEvent(db.Model):
    """Individual tracking event model"""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(20), nullable=False)  # 'open' or 'click'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    # Tracking data
    tracked_url = db.Column(db.Text)  # For click events
    user_agent = db.Column(db.Text)
    user_ip = db.Column(db.String(45))
    
    # Metadata (stored as JSON)
    metadata = db.Column(db.Text)

    def __repr__(self):
        return f'<TrackingEvent {self.event_type} at {self.timestamp}>'

# Email Tracking Service
class EmailTrackingService:
    """Service class for email tracking operations"""
    
    def __init__(self):
        self.config = TRACKING_CONFIG
    
    def create_campaign(self, name: str, subject: Optional[str] = None) -> Campaign:
        """Create a new email campaign"""
        campaign = Campaign(name=name, subject=subject)
        db.session.add(campaign)
        db.session.commit()
        return campaign
    
    def prepare_email(self, html_content: str, recipient_email: str, 
                     campaign_id: int, recipient_name: Optional[str] = None) -> tuple:
        """Prepare an HTML email with tracking links and pixels"""
        
        # Create email record
        email = Email(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            campaign_id=campaign_id
        )
        db.session.add(email)
        db.session.flush()  # Get the ID
        
        # Metadata for tracking
        metadata = {
            "email_id": email.id,
            "campaign_id": campaign_id,
            "recipient_email": recipient_email,
            "timestamp": int(time.time())
        }
        
        # Add tracking to HTML using pytracking's HTML adapter
        from pytracking.html import adapt_html
        tracked_html = adapt_html(
            html_content,
            extra_metadata=metadata,
            configuration=self.config
        )
        
        db.session.commit()
        return email, tracked_html
    
    def record_tracking_event(self, tracking_result: pytracking.TrackingResult):
        """Record a tracking event in the database"""
        if not tracking_result.metadata:
            return None
            
        metadata = tracking_result.metadata
        email_id = metadata.get('email_id')
        campaign_id = metadata.get('campaign_id')
        
        if not email_id:
            return None
        
        # Create tracking event
        event = TrackingEvent(
            event_type='open' if tracking_result.is_open_tracking else 'click',
            email_id=email_id,
            campaign_id=campaign_id,
            tracked_url=tracking_result.tracked_url,
            user_agent=tracking_result.request_data.get('user_agent') if tracking_result.request_data else None,
            user_ip=tracking_result.request_data.get('user_ip') if tracking_result.request_data else None,
            metadata=json.dumps(tracking_result.metadata)
        )
        db.session.add(event)
        
        # Update email record
        email = Email.query.get(email_id)
        if email:
            if tracking_result.is_open_tracking and not email.opened:
                email.opened = True
                email.first_opened_at = datetime.utcnow()
            elif tracking_result.is_click_tracking:
                email.clicks += 1
        
        db.session.commit()
        return event

# Initialize the service
tracking_service = EmailTrackingService()

# Flask Routes - Tracking Endpoints
@app.route('/track/open/<path:encoded_path>')
def track_open(encoded_path):
    """Handle open tracking requests"""
    request_data = {
        "user_agent": request.headers.get('User-Agent'),
        "user_ip": request.remote_addr,
        "referrer": request.headers.get('Referer')
    }
    
    try:
        # Decode tracking data
        tracking_result = pytracking.get_open_tracking_result(
            encoded_path,
            request_data=request_data,
            configuration=TRACKING_CONFIG
        )
        
        # Record the event
        tracking_service.record_tracking_event(tracking_result)
        
        # Return tracking pixel
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)
        
    except Exception as e:
        app.logger.error(f"Open tracking error: {e}")
        # Return pixel anyway to avoid broken images
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)

@app.route('/track/click/<path:encoded_path>')
def track_click(encoded_path):
    """Handle click tracking requests"""
    request_data = {
        "user_agent": request.headers.get('User-Agent'),
        "user_ip": request.remote_addr,
        "referrer": request.headers.get('Referer')
    }
    
    try:
        # Decode tracking data
        tracking_result = pytracking.get_click_tracking_result(
            encoded_path,
            request_data=request_data,
            configuration=TRACKING_CONFIG
        )
        
        # Record the event
        tracking_service.record_tracking_event(tracking_result)
        
        # Redirect to original URL
        if tracking_result.tracked_url:
            return redirect(tracking_result.tracked_url)
        else:
            return Response("Invalid tracking link", status=404)
        
    except Exception as e:
        app.logger.error(f"Click tracking error: {e}")
        return Response("Invalid tracking link", status=404)

@app.route('/webhook/tracking', methods=['POST'])
def webhook_tracking():
    """Handle webhook notifications (for external systems)"""
    try:
        data = request.get_json()
        app.logger.info(f"Webhook received: {data}")
        
        # You can forward this to other systems like analytics platforms
        # send_to_analytics_platform(data)
        
        return jsonify({"status": "received"}), 200
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 400

# Flask Routes - Web UI
@app.route('/')
def dashboard():
    """Main dashboard"""
    # Get summary statistics
    total_campaigns = Campaign.query.count()
    total_emails = Email.query.count()
    total_opens = TrackingEvent.query.filter_by(event_type='open').count()
    total_clicks = TrackingEvent.query.filter_by(event_type='click').count()
    
    # Recent campaigns
    recent_campaigns = Campaign.query.order_by(desc(Campaign.created_at)).limit(5).all()
    
    return render_template('dashboard.html',
                         total_campaigns=total_campaigns,
                         total_emails=total_emails,
                         total_opens=total_opens,
                         total_clicks=total_clicks,
                         recent_campaigns=recent_campaigns)

@app.route('/campaigns')
def campaigns():
    """List all campaigns"""
    campaigns_list = Campaign.query.order_by(desc(Campaign.created_at)).all()
    return render_template('campaigns.html', campaigns=campaigns_list)

@app.route('/campaigns/<int:campaign_id>')
def campaign_detail(campaign_id):
    """Campaign detail view"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get campaign statistics
    emails = Email.query.filter_by(campaign_id=campaign_id).all()
    opens = TrackingEvent.query.filter_by(campaign_id=campaign_id, event_type='open').count()
    clicks = TrackingEvent.query.filter_by(campaign_id=campaign_id, event_type='click').count()
    
    # Calculate rates
    open_rate = (opens / len(emails) * 100) if emails else 0
    click_rate = (clicks / len(emails) * 100) if emails else 0
    
    return render_template('campaign_detail.html',
                         campaign=campaign,
                         emails=emails,
                         opens=opens,
                         clicks=clicks,
                         open_rate=open_rate,
                         click_rate=click_rate)

@app.route('/create_campaign', methods=['GET', 'POST'])
def create_campaign():
    """Create new campaign"""
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form.get('subject', '')
        
        campaign = tracking_service.create_campaign(name, subject)
        return redirect(url_for('campaign_detail', campaign_id=campaign.id))
    
    return render_template('create_campaign.html')

@app.route('/send_test_email', methods=['GET', 'POST'])
def send_test_email():
    """Send a test email with tracking"""
    if request.method == 'POST':
        recipient = request.form['recipient']
        campaign_id = int(request.form['campaign_id'])
        
        # Sample HTML email
        html_content = """
        <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email with tracking.</p>
            <p><a href="https://example.com">Click here to visit our website</a></p>
            <p><a href="https://github.com">Or check out our GitHub</a></p>
        </body>
        </html>
        """
        
        # Prepare email with tracking
        email, tracked_html = tracking_service.prepare_email(
            html_content, recipient, campaign_id
        )
        
        # In a real application, you would send the email here
        # send_email(recipient, "Test Email", tracked_html)
        
        return render_template('email_preview.html', 
                             email=email, 
                             html_content=tracked_html,
                             message="Email prepared successfully! (Not actually sent in demo)")
    
    campaigns_list = Campaign.query.all()
    return render_template('send_test_email.html', campaigns=campaigns_list)

# API Routes
@app.route('/api/campaigns/<int:campaign_id>/stats')
def api_campaign_stats(campaign_id):
    """API endpoint for campaign statistics"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get daily stats for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_opens = db.session.query(
        func.date(TrackingEvent.timestamp).label('date'),
        func.count(TrackingEvent.id).label('count')
    ).filter(
        TrackingEvent.campaign_id == campaign_id,
        TrackingEvent.event_type == 'open',
        TrackingEvent.timestamp >= thirty_days_ago
    ).group_by(func.date(TrackingEvent.timestamp)).all()
    
    daily_clicks = db.session.query(
        func.date(TrackingEvent.timestamp).label('date'),
        func.count(TrackingEvent.id).label('count')
    ).filter(
        TrackingEvent.campaign_id == campaign_id,
        TrackingEvent.event_type == 'click',
        TrackingEvent.timestamp >= thirty_days_ago
    ).group_by(func.date(TrackingEvent.timestamp)).all()
    
    return jsonify({
        'campaign_id': campaign_id,
        'daily_opens': [{'date': str(d.date), 'count': d.count} for d in daily_opens],
        'daily_clicks': [{'date': str(d.date), 'count': d.count} for d in daily_clicks]
    })

@app.route('/api/events')
def api_recent_events():
    """API endpoint for recent tracking events"""
    limit = request.args.get('limit', 50, type=int)
    events = TrackingEvent.query.order_by(desc(TrackingEvent.timestamp)).limit(limit).all()
    
    return jsonify([{
        'id': event.id,
        'type': event.event_type,
        'timestamp': event.timestamp.isoformat(),
        'campaign_id': event.campaign_id,
        'email_id': event.email_id,
        'tracked_url': event.tracked_url,
        'user_agent': event.user_agent,
        'user_ip': event.user_ip
    } for event in events])

# Analytics Functions
def get_campaign_analytics(campaign_id: int) -> Dict:
    """Get comprehensive analytics for a campaign"""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return {}
    
    emails = Email.query.filter_by(campaign_id=campaign_id).all()
    opens = TrackingEvent.query.filter_by(campaign_id=campaign_id, event_type='open').count()
    clicks = TrackingEvent.query.filter_by(campaign_id=campaign_id, event_type='click').count()
    unique_opens = Email.query.filter_by(campaign_id=campaign_id, opened=True).count()
    
    # Top clicked URLs
    top_urls = db.session.query(
        TrackingEvent.tracked_url,
        func.count(TrackingEvent.id).label('clicks')
    ).filter(
        TrackingEvent.campaign_id == campaign_id,
        TrackingEvent.event_type == 'click',
        TrackingEvent.tracked_url.isnot(None)
    ).group_by(TrackingEvent.tracked_url).order_by(desc('clicks')).limit(10).all()
    
    return {
        'campaign': campaign,
        'total_emails': len(emails),
        'total_opens': opens,
        'unique_opens': unique_opens,
        'total_clicks': clicks,
        'open_rate': (unique_opens / len(emails) * 100) if emails else 0,
        'click_rate': (clicks / len(emails) * 100) if emails else 0,
        'top_urls': [(url, count) for url, count in top_urls]
    }

# CLI Commands for testing
def create_sample_data():
    """Create sample data for testing"""
    # Create sample campaign
    campaign = tracking_service.create_campaign("Newsletter 2024-01", "Welcome to our Newsletter!")
    
    # Create sample emails
    sample_recipients = [
        ("john@example.com", "John Doe"),
        ("jane@example.com", "Jane Smith"),
        ("bob@example.com", "Bob Johnson")
    ]
    
    html_content = """
    <html>
    <body>
        <h1>Welcome to Our Newsletter!</h1>
        <p>Thanks for subscribing. Here are some interesting links:</p>
        <ul>
            <li><a href="https://example.com/blog">Our Blog</a></li>
            <li><a href="https://example.com/products">Our Products</a></li>
            <li><a href="https://example.com/contact">Contact Us</a></li>
        </ul>
    </body>
    </html>
    """
    
    for email, name in sample_recipients:
        email_obj, tracked_html = tracking_service.prepare_email(
            html_content, email, campaign.id, name
        )
        print(f"Created email for {email} with ID {email_obj.id}")

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create sample data if database is empty
        if Campaign.query.count() == 0:
            create_sample_data()
            print("Sample data created!")
    
    print("Starting Email Tracking System...")
    print("Dashboard: http://localhost:5000")
    print("API Docs: Check the /api/ endpoints")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
