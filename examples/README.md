# Complete PyTracking Email Tracking System

This directory contains a complete, production-ready email tracking system built with PyTracking. It includes all the components needed for a real-world email tracking implementation.

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install pytracking[all] flask sqlalchemy flask-sqlalchemy requests
```

2. **Run the system:**
```bash
python complete_tracking_system.py
```

3. **Open your browser:**
   - Dashboard: http://localhost:5000
   - Create campaigns, send test emails, view analytics

## 📁 Components

### 1. Web Application (`complete_tracking_system.py`)
- **Flask-based web server** with full UI
- **SQLAlchemy database** for data persistence
- **Real-time tracking** endpoints
- **Analytics dashboard** with charts
- **Campaign management** interface
- **API endpoints** for external integration

### 2. CLI Tool (`tracking_cli.py`)
- **Command-line interface** for all operations
- **Generate tracking URLs** programmatically
- **Decode tracking data** for debugging
- **Test system functionality**
- **Create sample emails** with tracking

### 3. HTML Templates (`templates/`)
- **Responsive Bootstrap UI** with modern design
- **Real-time charts** using Chart.js
- **Mobile-friendly** interface
- **Dark/light theme** support

## 🎯 Features

### Core Tracking
- ✅ **Open Tracking** - 1x1 pixel tracking
- ✅ **Click Tracking** - Proxy URL redirects
- ✅ **Encryption** - Secure tracking data
- ✅ **Metadata** - Custom data attachment
- ✅ **Real-time** - Instant event processing

### Database & Analytics
- ✅ **SQLite database** (easily changeable to PostgreSQL/MySQL)
- ✅ **Campaign management** with statistics
- ✅ **Individual email tracking**
- ✅ **Event history** with full details
- ✅ **Analytics dashboard** with charts
- ✅ **Export capabilities** via API

### Web Interface
- ✅ **Modern responsive UI** with Bootstrap 5
- ✅ **Real-time dashboard** with live updates
- ✅ **Campaign creation** and management
- ✅ **Email preview** and testing
- ✅ **Analytics charts** and reports
- ✅ **API documentation** built-in

### Security & Performance
- ✅ **Encrypted tracking URLs** using Fernet
- ✅ **Rate limiting** protection
- ✅ **Error handling** and logging
- ✅ **HTTPS ready** for production
- ✅ **Webhook support** for external systems

## 🛠️ Usage Examples

### CLI Operations
```bash
# Create a campaign
python tracking_cli.py create-campaign "Newsletter 2024" --subject "Welcome!"

# Generate tracking pixel
python tracking_cli.py generate-pixel --campaign-id 1 --metadata '{"user_id": 123}'

# Generate tracking link
python tracking_cli.py generate-link "https://example.com" --campaign-id 1

# Generate sample email with tracking
python tracking_cli.py generate-email --campaign-id 1 --recipient "test@example.com"

# Run comprehensive test
python tracking_cli.py test
```

### Python Integration
```python
import pytracking
from complete_tracking_system import EmailTrackingService

# Initialize service
service = EmailTrackingService()

# Create campaign
campaign = service.create_campaign("My Campaign", "Subject Line")

# Prepare tracked email
email_obj, tracked_html = service.prepare_email(
    html_content="<html>...</html>",
    recipient_email="user@example.com",
    campaign_id=campaign.id
)

# Send with your ESP (SendGrid, Mailgun, etc.)
send_email(recipient, subject, tracked_html)
```

### API Integration
```javascript
// Get campaign statistics
fetch('/api/campaigns/1/stats')
  .then(response => response.json())
  .then(data => console.log(data));

// Get recent events
fetch('/api/events?limit=10')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🔧 Configuration

### Basic Configuration
```python
# In complete_tracking_system.py
TRACKING_CONFIG = pytracking.Configuration(
    base_open_tracking_url="https://yoursite.com/track/open/",
    base_click_tracking_url="https://yoursite.com/track/click/",
    webhook_url="https://yoursite.com/webhook/tracking",
    encryption_bytestring_key=your_encryption_key
)
```

### Database Configuration
```python
# SQLite (development)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_tracking.db'

# PostgreSQL (production)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/tracking'

# MySQL (production)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@localhost/tracking'
```

### Production Deployment
```python
# Use environment variables
import os

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# Enable production settings
app.config['DEBUG'] = False
```

## 📊 Database Schema

### Tables
1. **campaigns** - Email campaign information
2. **emails** - Individual email records
3. **tracking_events** - All tracking events (opens/clicks)

### Relationships
- Campaign → Many Emails
- Email → Many Tracking Events
- Campaign → Many Tracking Events (for analytics)

## 🔗 Integration with Email Service Providers

### SendGrid
```python
import sendgrid
from sendgrid.helpers.mail import Mail

def send_tracked_email(recipient, subject, tracked_html):
    message = Mail(
        from_email='noreply@yoursite.com',
        to_emails=recipient,
        subject=subject,
        html_content=tracked_html
    )
    
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    return response
```

### Mailgun
```python
import requests

def send_tracked_email(recipient, subject, tracked_html):
    return requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": "noreply@yoursite.com",
            "to": recipient,
            "subject": subject,
            "html": tracked_html
        }
    )
```

### Amazon SES
```python
import boto3

def send_tracked_email(recipient, subject, tracked_html):
    ses = boto3.client('ses', region_name='us-east-1')
    
    response = ses.send_email(
        Source='noreply@yoursite.com',
        Destination={'ToAddresses': [recipient]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': tracked_html}}
        }
    )
    return response
```

## 📈 Analytics & Reporting

### Built-in Analytics
- **Campaign performance** - Open rates, click rates, engagement
- **Real-time dashboard** - Live tracking events
- **Individual email tracking** - Per-recipient analytics
- **Time-based reports** - Daily, weekly, monthly trends
- **Link performance** - Most clicked URLs
- **Geographic data** - IP-based location tracking

### Export Options
- **JSON API** - Full data access via REST API
- **CSV export** - Campaign and event data
- **Webhook integration** - Real-time data streaming
- **Database direct access** - Custom queries

## 🔒 Security Considerations

### Data Protection
- **Encrypted tracking URLs** prevent data tampering
- **No sensitive data** in URLs (use metadata)
- **HTTPS enforcement** for all tracking endpoints
- **Rate limiting** prevents abuse
- **Input validation** on all endpoints

### Privacy Compliance
- **GDPR compliance** - User consent tracking
- **Data retention** policies configurable
- **Anonymization** options for IP addresses
- **Opt-out mechanisms** built-in

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "complete_tracking_system:app"]
```

### Environment Variables
```bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://user:pass@localhost/tracking"
export ENCRYPTION_KEY="your-base64-encryption-key"
export WEBHOOK_URL="https://yoursite.com/webhook"
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name tracking.yoursite.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Static files
    location /static {
        alias /app/static;
        expires 1y;
    }
}
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Tests
```bash
python tracking_cli.py test
```

### Load Testing
```bash
# Install wrk or ab
wrk -t12 -c400 -d30s http://localhost:5000/track/open/test
```

## 📚 Additional Resources

### Documentation
- [PyTracking Official Docs](https://github.com/powergo/pytracking)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### Email Marketing Best Practices
- Always get user consent for tracking
- Provide clear unsubscribe options
- Monitor bounce rates and deliverability
- A/B test different email designs
- Segment your audience for better engagement

### Performance Optimization
- Use connection pooling for database
- Implement caching for frequently accessed data
- Optimize tracking pixel size (already 1x1)
- Use CDN for static assets
- Monitor and log performance metrics

## 🤝 Contributing

This is a complete example implementation. Feel free to:
- Extend functionality for your specific needs
- Add new analytics features
- Improve the UI/UX
- Add more ESP integrations
- Enhance security features

## 📄 License

This example is provided as-is for educational and development purposes. Please ensure compliance with privacy laws (GDPR, CCPA, etc.) when implementing email tracking in production.
