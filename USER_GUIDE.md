# PyTracking User Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Configuration](#configuration)
- [Open Tracking](#open-tracking)
- [Click Tracking](#click-tracking)
- [HTML Email Processing](#html-email-processing)
- [Encryption](#encryption)
- [Django Integration](#django-integration)
- [Webhook Integration](#webhook-integration)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

## Quick Start

### Basic Example

```python
import pytracking

# Create configuration
config = pytracking.Configuration(
    base_open_tracking_url="https://realproductpat.com/track/open/",
    base_click_tracking_url="https://realproductpat.com/track/click/"
)

# Generate an open tracking pixel URL
open_tracking_url = pytracking.get_open_tracking_url(
    configuration=config,
    metadata={"user_id": "123", "campaign_id": "summer2023"}
)

# Generate a click tracking URL
click_tracking_url = pytracking.get_click_tracking_url(
    "https://realproductpat.com/products/shoes",
    configuration=config,
    metadata={"user_id": "123", "product_id": "shoe_456"}
)

print(f"Open tracking URL: {open_tracking_url}")
print(f"Click tracking URL: {click_tracking_url}")
```

### Complete Email Example

```python
import pytracking

def create_tracked_email():
    config = pytracking.Configuration(
        base_open_tracking_url="https://realproductpat.com/track/open/",
        base_click_tracking_url="https://realproductpat.com/track/click/"
    )
    
    # Email metadata
    metadata = {
        "user_id": "user_123",
        "campaign_id": "newsletter_2023_07",
        "email_type": "promotional"
    }
    
    # Create tracking URLs
    open_pixel = pytracking.get_open_tracking_url(config, metadata=metadata)
    shop_now_link = pytracking.get_click_tracking_url(
        "https://realproductpat.com/shop", config, metadata=metadata
    )
    
    # HTML email template
    html_email = f"""
    <html>
    <body>
        <h1>Summer Sale!</h1>
        <p>Don't miss our amazing summer deals!</p>
        <a href="{shop_now_link}">Shop Now</a>
        
        <!-- Tracking pixel (invisible) -->
        <img src="{open_pixel}" width="1" height="1" style="display:none;" />
    </body>
    </html>
    """
    
    return html_email

email_html = create_tracked_email()
print(email_html)
```

## Core Concepts

### Stateless Tracking
PyTracking uses a stateless approach where all tracking information is encoded directly in the URL. This means:
- No database storage required for tracking links
- Each URL contains all necessary information
- Easy to scale and distribute
- URLs can be long but are self-contained

### Tracking Types

#### 1. Open Tracking
- Uses a 1x1 transparent pixel image
- Triggered when email client loads the image
- Indicates email was opened (with caveats*)

#### 2. Click Tracking
- Replaces original links with tracking URLs
- Redirects to original URL after logging the click
- Provides click-through analytics

*Note: Open tracking has limitations due to email client behavior, image blocking, and privacy features.*

### Metadata
Arbitrary data you want to associate with tracking events:
```python
metadata = {
    "user_id": "12345",
    "campaign_id": "summer_sale",
    "email_template": "promotional_v2",
    "custom_field": "any_value"
}
```

## Configuration

### Basic Configuration

```python
import pytracking

config = pytracking.Configuration(
    base_open_tracking_url="https://realproductpat.com/track/open/",
    base_click_tracking_url="https://realproductpat.com/track/click/",
    webhook_url="https://realproductpat.com/webhooks/tracking/",
    default_metadata={"source": "email_campaign"}
)
```

### Configuration Options

```python
config = pytracking.Configuration(
    # Required: Base URLs for tracking endpoints
    base_open_tracking_url="https://realproductpat.com/track/open/",
    base_click_tracking_url="https://realproductpat.com/track/click/",
    
    # Optional: Webhook configuration
    webhook_url="https://realproductpat.com/webhooks/tracking/",
    webhook_timeout_seconds=5,
    include_webhook_url=False,  # Include webhook URL in encoded data
    
    # Optional: Default metadata
    default_metadata={"source": "email"},
    include_default_metadata=True,  # Include in encoded data
    
    # Optional: Encryption
    encryption_bytestring_key=None,  # Fernet encryption key
    
    # Optional: Encoding settings
    encoding="utf-8",
    append_slash=True
)
```

### Dynamic Configuration

```python
# Base configuration
base_config = pytracking.Configuration(
    base_open_tracking_url="https://realproductpat.com/track/open/"
)

# Override specific parameters
tracking_url = pytracking.get_open_tracking_url(
    configuration=base_config,
    metadata={"user_id": "123"},
    # Override webhook for this specific tracking
    webhook_url="https://special-webhook.com/track/"
)
```

## Open Tracking

### Basic Open Tracking

```python
import pytracking

config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/"
)

# Generate tracking URL
tracking_url = pytracking.get_open_tracking_url(
    configuration=config,
    metadata={"user_id": "123", "email_id": "456"}
)

# Use in HTML email
html = f'<img src="{tracking_url}" width="1" height="1" style="display:none;" />'
```

### Get Tracking Pixel Binary

```python
# Get the actual pixel image data
pixel_data, mime_type = pytracking.get_open_tracking_pixel()
print(f"Pixel size: {len(pixel_data)} bytes")
print(f"MIME type: {mime_type}")  # "image/png"

# Save pixel to file (for reference)
with open("tracking_pixel.png", "wb") as f:
    f.write(pixel_data)
```

### Processing Open Tracking Requests

When someone opens an email, handle the request on your server:

```python
def handle_open_tracking(request_path):
    """Handle open tracking requests from email clients."""
    
    # Extract tracking data from URL path
    result = pytracking.get_open_tracking_result(
        tracking_url_path=request_path,
        configuration=config
    )
    
    if result:
        print(f"Email opened!")
        print(f"Metadata: {result.metadata}")
        print(f"Tracking data: {result.tracking_result}")
        
        # Your logic here: save to database, send to analytics, etc.
        save_open_event(result.metadata)
        
        # Return the tracking pixel
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return pixel_data, mime_type
    else:
        # Invalid tracking URL
        return None, None

# Example usage
request_path = "/track/open/eyJ0eXAiOiJKV1QiLCJhbGciOi..."
pixel_data, mime_type = handle_open_tracking(request_path)
```

## Click Tracking

### Basic Click Tracking

```python
import pytracking

config = pytracking.Configuration(
    base_click_tracking_url="https://yourdomain.com/track/click/"
)

# Original URL you want to track
original_url = "https://yourdomain.com/products/shoes"

# Generate tracking URL
tracking_url = pytracking.get_click_tracking_url(
    original_url,
    configuration=config,
    metadata={"user_id": "123", "product_id": "shoes_456"}
)

print(f"Original: {original_url}")
print(f"Tracking: {tracking_url}")
```

### Processing Click Tracking Requests

When someone clicks a tracking link:

```python
def handle_click_tracking(request_path):
    """Handle click tracking requests and redirect to original URL."""
    
    # Extract tracking data and original URL
    result = pytracking.get_click_tracking_result(
        tracking_url_path=request_path,
        configuration=config
    )
    
    if result:
        print(f"Link clicked!")
        print(f"Original URL: {result.tracked_url}")
        print(f"Metadata: {result.metadata}")
        
        # Your logic here: save to database, send to analytics, etc.
        save_click_event(result.metadata, result.tracked_url)
        
        # Redirect to original URL
        return result.tracked_url
    else:
        # Invalid tracking URL - redirect to homepage or show error
        return "https://yourdomain.com/"

# Example usage
request_path = "/track/click/eyJ0eXAiOiJKV1QiLCJhbGciOi..."
redirect_url = handle_click_tracking(request_path)
print(f"Redirect to: {redirect_url}")
```

### Advanced Click Tracking

```python
# Track different link types with specific metadata
def create_tracked_links(base_config):
    links = {}
    
    # Product link
    links['product'] = pytracking.get_click_tracking_url(
        "https://shop.com/products/123",
        configuration=base_config,
        metadata={
            "link_type": "product",
            "product_id": "123",
            "position": "main_cta"
        }
    )
    
    # Social media link
    links['social'] = pytracking.get_click_tracking_url(
        "https://facebook.com/yourpage",
        configuration=base_config,
        metadata={
            "link_type": "social",
            "platform": "facebook",
            "position": "footer"
        }
    )
    
    # Unsubscribe link
    links['unsubscribe'] = pytracking.get_click_tracking_url(
        "https://yourdomain.com/unsubscribe?user=123",
        configuration=base_config,
        metadata={
            "link_type": "unsubscribe",
            "user_id": "123"
        }
    )
    
    return links
```

## HTML Email Processing

PyTracking can automatically modify HTML emails to add tracking. This requires the `html` extra: `pip install pytracking[html]`

### Automatic HTML Processing

```python
import pytracking.html

config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    base_click_tracking_url="https://yourdomain.com/track/click/"
)

# Original HTML email
original_html = """
<html>
<body>
    <h1>Welcome!</h1>
    <p>Check out our <a href="https://shop.com/products">latest products</a>!</p>
    <p>Follow us on <a href="https://twitter.com/yourcompany">Twitter</a></p>
    <p><a href="https://yourdomain.com/unsubscribe">Unsubscribe</a></p>
</body>
</html>
"""

# Automatically add tracking to all links and add open tracking pixel
tracked_html = pytracking.html.modify_html(
    original_html,
    configuration=config,
    metadata={"user_id": "123", "campaign_id": "welcome"}
)

print(tracked_html)
```

### Selective Link Tracking

```python
# Only track specific links by adding CSS classes or attributes
html_with_classes = """
<html>
<body>
    <h1>Welcome!</h1>
    <p>Check out our <a href="https://shop.com/products" class="track-click">latest products</a>!</p>
    <p>Follow us on <a href="https://twitter.com/yourcompany">Twitter</a> (not tracked)</p>
    <p><a href="https://yourdomain.com/unsubscribe" data-track="true">Unsubscribe</a></p>
</body>
</html>
"""

# Configure which links to track
tracked_html = pytracking.html.modify_html(
    html_with_classes,
    configuration=config,
    metadata={"user_id": "123"},
    # Only track links with class "track-click" or attribute "data-track"
    selector=".track-click, [data-track]"
)
```

### Custom Link Processing

```python
def custom_link_processor(url, metadata):
    """Custom logic for processing different types of links."""
    
    if "shop.com" in url:
        # Add specific metadata for shop links
        metadata.update({
            "link_type": "product",
            "domain": "shop"
        })
    elif "twitter.com" in url or "facebook.com" in url:
        # Add social media tracking
        metadata.update({
            "link_type": "social",
            "platform": "twitter" if "twitter.com" in url else "facebook"
        })
    elif "unsubscribe" in url:
        # Special handling for unsubscribe
        metadata.update({
            "link_type": "unsubscribe",
            "critical": True
        })
    
    return metadata

# Use custom processor
tracked_html = pytracking.html.modify_html(
    original_html,
    configuration=config,
    metadata={"user_id": "123"},
    link_processor=custom_link_processor
)
```

## Encryption

Protect your tracking data from tampering and inspection with encryption. Requires the `crypto` extra: `pip install pytracking[crypto]`

### Setting Up Encryption

```python
from cryptography.fernet import Fernet
import pytracking

# Generate encryption key (do this once, store securely)
encryption_key = Fernet.generate_key()
print(f"Store this key securely: {encryption_key}")

# Configuration with encryption
config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    base_click_tracking_url="https://yourdomain.com/track/click/",
    encryption_bytestring_key=encryption_key
)

# URLs generated with this config will be encrypted
encrypted_url = pytracking.get_open_tracking_url(
    configuration=config,
    metadata={"user_id": "123", "sensitive_data": "secret"}
)

print(f"Encrypted tracking URL: {encrypted_url}")
```

### Key Management

```python
import os
from cryptography.fernet import Fernet

class EncryptionKeyManager:
    @staticmethod
    def generate_key():
        """Generate a new encryption key."""
        return Fernet.generate_key()
    
    @staticmethod
    def load_key_from_env():
        """Load encryption key from environment variable."""
        key = os.environ.get('PYTRACKING_ENCRYPTION_KEY')
        if not key:
            raise ValueError("PYTRACKING_ENCRYPTION_KEY environment variable not set")
        return key.encode() if isinstance(key, str) else key
    
    @staticmethod
    def load_key_from_file(filepath):
        """Load encryption key from file."""
        with open(filepath, 'rb') as f:
            return f.read()
    
    @staticmethod
    def save_key_to_file(key, filepath):
        """Save encryption key to file."""
        with open(filepath, 'wb') as f:
            f.write(key)

# Usage
key_manager = EncryptionKeyManager()

# Generate and save key (do once)
# key = key_manager.generate_key()
# key_manager.save_key_to_file(key, '/secure/path/tracking.key')

# Load key in your application
encryption_key = key_manager.load_key_from_env()
# or
# encryption_key = key_manager.load_key_from_file('/secure/path/tracking.key')

config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    encryption_bytestring_key=encryption_key
)
```

### Encrypted vs Unencrypted URLs

```python
# Without encryption (base64 encoded, readable)
config_plain = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/"
)

plain_url = pytracking.get_open_tracking_url(
    configuration=config_plain,
    metadata={"user_id": "123"}
)

# With encryption (encrypted, not readable)
config_encrypted = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    encryption_bytestring_key=Fernet.generate_key()
)

encrypted_url = pytracking.get_open_tracking_url(
    configuration=config_encrypted,
    metadata={"user_id": "123"}
)

print(f"Plain URL: {plain_url}")
print(f"Encrypted URL: {encrypted_url}")
```

## Django Integration

PyTracking provides Django views and helpers for easy integration. Requires the `django` extra: `pip install pytracking[django]`

### Django Views

```python
# views.py
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
import pytracking
import pytracking.django

class OpenTrackingView(pytracking.django.OpenTrackingView):
    """Handle open tracking requests."""
    
    def get_configuration(self):
        """Return tracking configuration."""
        return pytracking.Configuration(
            base_open_tracking_url="https://yourdomain.com/track/open/",
            encryption_bytestring_key=settings.TRACKING_ENCRYPTION_KEY
        )
    
    def notify_tracking_event(self, tracking_result):
        """Called when tracking event occurs."""
        # Your custom logic here
        print(f"Email opened: {tracking_result.metadata}")
        
        # Save to database
        from .models import EmailOpen
        EmailOpen.objects.create(
            user_id=tracking_result.metadata.get('user_id'),
            campaign_id=tracking_result.metadata.get('campaign_id'),
            timestamp=timezone.now(),
            user_agent=tracking_result.request_data.get('user_agent'),
            ip_address=tracking_result.request_data.get('user_ip')
        )

class ClickTrackingView(pytracking.django.ClickTrackingView):
    """Handle click tracking requests."""
    
    def get_configuration(self):
        """Return tracking configuration."""
        return pytracking.Configuration(
            base_click_tracking_url="https://yourdomain.com/track/click/",
            encryption_bytestring_key=settings.TRACKING_ENCRYPTION_KEY
        )
    
    def notify_tracking_event(self, tracking_result):
        """Called when tracking event occurs."""
        print(f"Link clicked: {tracking_result.metadata}")
        print(f"Original URL: {tracking_result.tracked_url}")
        
        # Save to database
        from .models import EmailClick
        EmailClick.objects.create(
            user_id=tracking_result.metadata.get('user_id'),
            original_url=tracking_result.tracked_url,
            link_type=tracking_result.metadata.get('link_type'),
            timestamp=timezone.now(),
            user_agent=tracking_result.request_data.get('user_agent'),
            ip_address=tracking_result.request_data.get('user_ip')
        )
```

### Django URLs

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('track/open/<path:encoded_data>/', 
         views.OpenTrackingView.as_view(), 
         name='open_tracking'),
    path('track/click/<path:encoded_data>/', 
         views.ClickTrackingView.as_view(), 
         name='click_tracking'),
]
```

### Django Settings

```python
# settings.py
import os
from cryptography.fernet import Fernet

# Tracking configuration
TRACKING_ENCRYPTION_KEY = os.environ.get('TRACKING_ENCRYPTION_KEY', '').encode()

# If no key is set, generate one (for development only)
if not TRACKING_ENCRYPTION_KEY:
    TRACKING_ENCRYPTION_KEY = Fernet.generate_key()
    print(f"Generated tracking key: {TRACKING_ENCRYPTION_KEY}")

# Base URLs for tracking
TRACKING_BASE_OPEN_URL = "https://yourdomain.com/track/open/"
TRACKING_BASE_CLICK_URL = "https://yourdomain.com/track/click/"
```

### Django Models

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class EmailCampaign(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
class EmailOpen(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_id_str = models.CharField(max_length=100)  # For non-User tracking
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, null=True)
    campaign_id_str = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
class EmailClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_id_str = models.CharField(max_length=100)
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, null=True)
    campaign_id_str = models.CharField(max_length=100)
    original_url = models.URLField()
    link_type = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
```

### Django Email Service

```python
# services.py
from django.conf import settings
from django.core.mail import send_mail
import pytracking
import pytracking.html

class EmailTrackingService:
    def __init__(self):
        self.config = pytracking.Configuration(
            base_open_tracking_url=settings.TRACKING_BASE_OPEN_URL,
            base_click_tracking_url=settings.TRACKING_BASE_CLICK_URL,
            encryption_bytestring_key=settings.TRACKING_ENCRYPTION_KEY
        )
    
    def send_tracked_email(self, to_email, subject, html_content, user_id, campaign_id):
        """Send an email with tracking."""
        
        metadata = {
            "user_id": str(user_id),
            "campaign_id": str(campaign_id),
            "email": to_email
        }
        
        # Add tracking to HTML content
        tracked_html = pytracking.html.modify_html(
            html_content,
            configuration=self.config,
            metadata=metadata
        )
        
        # Send email
        send_mail(
            subject=subject,
            message="",  # Plain text version
            html_message=tracked_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email]
        )
        
        return True

# Usage
email_service = EmailTrackingService()
email_service.send_tracked_email(
    to_email="user@example.com",
    subject="Welcome to our service!",
    html_content="<h1>Welcome!</h1><p>Click <a href='https://oursite.com/products'>here</a> to shop.</p>",
    user_id=123,
    campaign_id=456
)
```

## Webhook Integration

Send tracking data to external services using webhooks. Requires the `webhook` extra: `pip install pytracking[webhook]`

### Basic Webhook Usage

```python
import pytracking.webhook

config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    webhook_url="https://yourdomain.com/webhooks/tracking/",
    webhook_timeout_seconds=10
)

# When processing tracking events
def handle_tracking_event(tracking_result):
    # Send data to webhook
    response = pytracking.webhook.notify_webhook(
        configuration=config,
        tracking_result=tracking_result
    )
    
    if response and response.status_code == 200:
        print("Webhook notification successful")
    else:
        print("Webhook notification failed")
```

### Custom Webhook Payloads

```python
import requests
import json

def send_custom_webhook(tracking_result, webhook_url):
    """Send custom webhook payload."""
    
    payload = {
        "event_type": "email_open",
        "timestamp": time.time(),
        "user_data": tracking_result.metadata,
        "request_info": tracking_result.request_data,
        "custom_field": "additional_data"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Source": "pytracking",
        "Authorization": "Bearer your-webhook-token"
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        return response
    except requests.RequestException as e:
        print(f"Webhook error: {e}")
        return None
```

### Webhook Error Handling

```python
import logging
from requests.exceptions import RequestException

def robust_webhook_notification(tracking_result, webhook_url, max_retries=3):
    """Send webhook with retry logic."""
    
    for attempt in range(max_retries):
        try:
            response = pytracking.webhook.notify_webhook(
                configuration=config,
                tracking_result=tracking_result
            )
            
            if response and response.status_code == 200:
                logging.info("Webhook notification successful")
                return True
            else:
                logging.warning(f"Webhook returned status {response.status_code if response else 'None'}")
                
        except RequestException as e:
            logging.warning(f"Webhook attempt {attempt + 1} failed: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    logging.error("All webhook attempts failed")
    return False
```

## Advanced Usage

### Multiple Configurations

```python
# Different configurations for different purposes
configs = {
    "promotional": pytracking.Configuration(
        base_open_tracking_url="https://track.yourdomain.com/promo/open/",
        base_click_tracking_url="https://track.yourdomain.com/promo/click/",
        webhook_url="https://analytics.yourdomain.com/promo-webhook/",
        default_metadata={"type": "promotional"}
    ),
    
    "transactional": pytracking.Configuration(
        base_open_tracking_url="https://track.yourdomain.com/trans/open/",
        base_click_tracking_url="https://track.yourdomain.com/trans/click/",
        webhook_url="https://analytics.yourdomain.com/trans-webhook/",
        default_metadata={"type": "transactional"}
    ),
    
    "newsletter": pytracking.Configuration(
        base_open_tracking_url="https://track.yourdomain.com/news/open/",
        base_click_tracking_url="https://track.yourdomain.com/news/click/",
        default_metadata={"type": "newsletter"}
    )
}

# Use appropriate config
def send_email(email_type, content, metadata):
    config = configs[email_type]
    tracked_url = pytracking.get_open_tracking_url(
        configuration=config,
        metadata=metadata
    )
    # Send email...
```

### Batch Processing

```python
def create_tracking_urls_batch(urls_and_metadata, config):
    """Create multiple tracking URLs efficiently."""
    
    tracking_urls = []
    
    for url_data in urls_and_metadata:
        if url_data["type"] == "open":
            tracking_url = pytracking.get_open_tracking_url(
                configuration=config,
                metadata=url_data["metadata"]
            )
        elif url_data["type"] == "click":
            tracking_url = pytracking.get_click_tracking_url(
                url_data["original_url"],
                configuration=config,
                metadata=url_data["metadata"]
            )
        
        tracking_urls.append({
            "original": url_data.get("original_url"),
            "tracking": tracking_url,
            "metadata": url_data["metadata"]
        })
    
    return tracking_urls

# Example usage
batch_data = [
    {
        "type": "open",
        "metadata": {"user_id": "123", "email_id": "456"}
    },
    {
        "type": "click",
        "original_url": "https://shop.com/products",
        "metadata": {"user_id": "123", "link_type": "product"}
    },
    {
        "type": "click", 
        "original_url": "https://shop.com/sale",
        "metadata": {"user_id": "123", "link_type": "sale"}
    }
]

tracked_urls = create_tracking_urls_batch(batch_data, config)
```

### Analytics Integration

```python
import json
from datetime import datetime

class TrackingAnalytics:
    def __init__(self, config):
        self.config = config
        self.events = []
    
    def process_open_event(self, tracking_result):
        """Process an email open event."""
        event = {
            "type": "open",
            "timestamp": datetime.now().isoformat(),
            "metadata": tracking_result.metadata,
            "request_data": tracking_result.request_data
        }
        
        self.events.append(event)
        self._send_to_analytics(event)
    
    def process_click_event(self, tracking_result):
        """Process a link click event."""
        event = {
            "type": "click",
            "timestamp": datetime.now().isoformat(),
            "original_url": tracking_result.tracked_url,
            "metadata": tracking_result.metadata,
            "request_data": tracking_result.request_data
        }
        
        self.events.append(event)
        self._send_to_analytics(event)
    
    def _send_to_analytics(self, event):
        """Send event to analytics service."""
        # Integration with Google Analytics, Mixpanel, etc.
        pass
    
    def get_campaign_stats(self, campaign_id):
        """Get statistics for a specific campaign."""
        campaign_events = [
            e for e in self.events 
            if e["metadata"].get("campaign_id") == campaign_id
        ]
        
        opens = len([e for e in campaign_events if e["type"] == "open"])
        clicks = len([e for e in campaign_events if e["type"] == "click"])
        
        return {
            "campaign_id": campaign_id,
            "total_opens": opens,
            "total_clicks": clicks,
            "click_through_rate": clicks / opens if opens > 0 else 0
        }
```

### URL Validation and Security

```python
import urllib.parse
from urllib.parse import urlparse

def validate_tracking_url(url, allowed_domains):
    """Validate tracking URLs for security."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain is allowed
        if not any(domain.endswith(allowed) for allowed in allowed_domains):
            raise ValueError(f"Domain {domain} not allowed")
        
        # Check for suspicious patterns
        if any(suspicious in url.lower() for suspicious in ['javascript:', 'data:', 'vbscript:']):
            raise ValueError("Suspicious URL scheme detected")
        
        return True
        
    except Exception as e:
        print(f"URL validation failed: {e}")
        return False

def safe_click_tracking(original_url, config, metadata):
    """Create click tracking URL with validation."""
    allowed_domains = ['yourdomain.com', 'shop.yourdomain.com', 'blog.yourdomain.com']
    
    if not validate_tracking_url(original_url, allowed_domains):
        # Return original URL without tracking if validation fails
        return original_url
    
    return pytracking.get_click_tracking_url(
        original_url,
        configuration=config,
        metadata=metadata
    )
```

## Best Practices

### Security

1. **Use Encryption**: Always encrypt sensitive tracking data
```python
config = pytracking.Configuration(
    encryption_bytestring_key=your_secret_key,
    # ... other settings
)
```

2. **Validate URLs**: Check original URLs before creating tracking links
3. **Rate Limiting**: Implement rate limiting on tracking endpoints
4. **HTTPS Only**: Always use HTTPS for tracking URLs

### Performance

1. **Cache Configuration Objects**: Reuse configuration objects
```python
# Good: Reuse config
config = pytracking.Configuration(...)
for email in emails:
    url = pytracking.get_open_tracking_url(configuration=config, ...)

# Avoid: Creating new config each time
for email in emails:
    config = pytracking.Configuration(...)  # Inefficient
    url = pytracking.get_open_tracking_url(configuration=config, ...)
```

2. **Batch Processing**: Process multiple URLs together when possible
3. **Async Webhooks**: Use async processing for webhook notifications

### Data Management

1. **Minimal Metadata**: Only include necessary data in tracking URLs
2. **Data Retention**: Implement policies for tracking data retention
3. **Privacy Compliance**: Ensure compliance with GDPR, CCPA, etc.

### Monitoring

1. **Error Tracking**: Monitor webhook failures and tracking errors
2. **Performance Metrics**: Track response times for tracking endpoints
3. **Analytics**: Monitor open rates, click rates, and engagement metrics

### Email Client Compatibility

1. **Pixel Placement**: Place tracking pixels at the end of emails
2. **Link Testing**: Test tracking links across different email clients
3. **Fallback Handling**: Provide fallbacks for when tracking fails

## API Reference

### Configuration Class

```python
class Configuration:
    def __init__(
        self,
        webhook_url=None,
        webhook_timeout_seconds=5,
        include_webhook_url=False,
        base_open_tracking_url=None,
        base_click_tracking_url=None,
        default_metadata=None,
        include_default_metadata=False,
        encryption_bytestring_key=None,
        encoding="utf-8",
        append_slash=False,
        **kwargs
    )
```

### Core Functions

#### `get_open_tracking_url(configuration, metadata=None, **kwargs)`
Generate a URL for tracking email opens.

**Parameters:**
- `configuration`: Configuration object
- `metadata`: Dictionary of tracking data
- `**kwargs`: Override configuration parameters

**Returns:** Tracking URL string

#### `get_click_tracking_url(tracked_url, configuration, metadata=None, **kwargs)`
Generate a URL for tracking link clicks.

**Parameters:**
- `tracked_url`: Original URL to track
- `configuration`: Configuration object  
- `metadata`: Dictionary of tracking data
- `**kwargs`: Override configuration parameters

**Returns:** Tracking URL string

#### `get_open_tracking_result(tracking_url_path, configuration, **kwargs)`
Decode open tracking data from URL path.

**Parameters:**
- `tracking_url_path`: URL path containing encoded data
- `configuration`: Configuration object
- `**kwargs`: Override configuration parameters

**Returns:** TrackingResult object or None

#### `get_click_tracking_result(tracking_url_path, configuration, **kwargs)`
Decode click tracking data from URL path.

**Parameters:**
- `tracking_url_path`: URL path containing encoded data
- `configuration`: Configuration object
- `**kwargs`: Override configuration parameters

**Returns:** TrackingResult object or None

#### `get_open_tracking_pixel()`
Get the tracking pixel image data.

**Returns:** Tuple of (image_bytes, mime_type)

### TrackingResult Class

```python
class TrackingResult:
    metadata          # Dictionary of tracking metadata
    tracking_result   # Decoded tracking information
    request_data      # Request information (IP, User-Agent, etc.)
    tracked_url       # Original URL (for click tracking only)
```

### HTML Processing

#### `pytracking.html.modify_html(html, configuration, metadata=None, **kwargs)`
Automatically add tracking to HTML emails.

**Parameters:**
- `html`: HTML content string
- `configuration`: Configuration object
- `metadata`: Dictionary of tracking data
- `**kwargs`: Additional options

**Returns:** Modified HTML string

### Django Views

#### `pytracking.django.OpenTrackingView`
Django view for handling open tracking requests.

#### `pytracking.django.ClickTrackingView`
Django view for handling click tracking requests.

### Webhook Functions

#### `pytracking.webhook.notify_webhook(configuration, tracking_result)`
Send tracking data to a webhook.

**Parameters:**
- `configuration`: Configuration object with webhook URL
- `tracking_result`: TrackingResult object

**Returns:** HTTP response object or None

---

This user guide covers the essential features and usage patterns of PyTracking. For the most up-to-date information, always refer to the official documentation and source code.
