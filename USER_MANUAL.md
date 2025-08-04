# PyTracking - Comprehensive User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Quick Start Guide](#quick-start-guide)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Features and Usage](#features-and-usage)
8. [Advanced Topics](#advanced-topics)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)
12. [Contributing](#contributing)

---

## Introduction

PyTracking is a Python library that provides email open and click tracking functionality. It's designed for applications that need to track user engagement with emails when using Email Service Providers (ESPs) that don't provide built-in tracking capabilities.

### Key Features

- **Stateless Tracking**: All tracking information is encoded in URLs
- **Open Tracking**: Track when emails are opened using transparent 1x1 pixels
- **Click Tracking**: Track link clicks with proxy URLs that redirect to original destinations
- **Encryption Support**: Optional encryption of tracking data for security
- **Django Integration**: Pre-built Django views for handling tracking requests
- **HTML Processing**: Automatic modification of HTML emails to add tracking
- **Webhook Support**: Automated notifications to webhooks when tracking events occur
- **Metadata Support**: Attach custom data to tracking links

### How It Works

PyTracking implements a stateless tracking strategy:

1. **Encoding Phase**: Tracking information (metadata, URLs, webhooks) is encoded into base64 or encrypted strings
2. **Email Integration**: These encoded strings are embedded in email pixels (open tracking) or proxy URLs (click tracking)
3. **Decoding Phase**: When users interact with emails, your server receives requests with encoded data
4. **Processing**: PyTracking decodes the data and provides structured information about the tracking event

---

## Installation

### Basic Installation

```bash
pip install pytracking
```

### Feature-Specific Installation

Install with specific optional features:

```bash
# Django support
pip install pytracking[django]

# Encryption support
pip install pytracking[crypto]

# HTML processing support
pip install pytracking[html]

# Webhook support
pip install pytracking[webhook]

# All features
pip install pytracking[all]
```

### Requirements

- Python 3.6+
- No required dependencies for basic functionality
- Optional dependencies based on features used

---

## Core Concepts

### Tracking Types

1. **Open Tracking**: Uses invisible 1x1 pixel images to detect when emails are opened
2. **Click Tracking**: Replaces original URLs with proxy URLs that track clicks before redirecting

### Configuration Object

The `Configuration` class centralizes settings for tracking operations:

```python
from pytracking import Configuration

config = Configuration(
    base_open_tracking_url="https://tracking.example.com/open/",
    base_click_tracking_url="https://tracking.example.com/click/",
    webhook_url="https://api.example.com/webhook",
    default_metadata={"source": "newsletter"},
    encryption_bytestring_key=encryption_key  # Optional
)
```

### TrackingResult Object

Contains decoded tracking information:

- `is_open_tracking`: Boolean indicating if this is an open tracking event
- `is_click_tracking`: Boolean indicating if this is a click tracking event
- `tracked_url`: Original URL (for click tracking)
- `webhook_url`: URL to notify about the event
- `metadata`: Associated metadata dictionary
- `request_data`: Information about the client request
- `timestamp`: Unix timestamp of the event

---

## Quick Start Guide

### 1. Basic Open Tracking

```python
import pytracking

# Generate an open tracking URL
open_url = pytracking.get_open_tracking_url(
    metadata={"user_id": 12345, "campaign": "newsletter"},
    base_open_tracking_url="https://tracking.example.com/open/"
)

# The URL will look like: https://tracking.example.com/open/eyJtZXRhZGF0YSI6...
print(f"Open tracking pixel: <img src='{open_url}' width='1' height='1' />")
```

### 2. Basic Click Tracking

```python
import pytracking

# Generate a click tracking URL
click_url = pytracking.get_click_tracking_url(
    url_to_track="https://example.com/product/123",
    metadata={"user_id": 12345, "product": "123"},
    base_click_tracking_url="https://tracking.example.com/click/"
)

print(f"Click tracking link: <a href='{click_url}'>Visit Product</a>")
```

### 3. Handling Tracking Events

```python
import pytracking

# When your server receives a tracking request
def handle_open_tracking(request_path):
    tracking_result = pytracking.get_open_tracking_result(
        request_path,
        base_open_tracking_url="https://tracking.example.com/open/"
    )
    
    print(f"Email opened by user: {tracking_result.metadata.get('user_id')}")
    return tracking_result

def handle_click_tracking(request_path):
    tracking_result = pytracking.get_click_tracking_result(
        request_path,
        base_click_tracking_url="https://tracking.example.com/click/"
    )
    
    print(f"Link clicked: {tracking_result.tracked_url}")
    print(f"User: {tracking_result.metadata.get('user_id')}")
    
    # Redirect user to original URL
    return tracking_result.tracked_url
```

---

## Configuration

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `webhook_url` | str | None | URL to notify when tracking events occur |
| `webhook_timeout_seconds` | int | 5 | Timeout for webhook requests |
| `include_webhook_url` | bool | False | Whether to encode webhook URL in tracking links |
| `base_open_tracking_url` | str | None | Base URL for open tracking links |
| `base_click_tracking_url` | str | None | Base URL for click tracking links |
| `default_metadata` | dict | None | Default metadata for all tracking events |
| `include_default_metadata` | bool | False | Whether to encode default metadata in links |
| `encryption_bytestring_key` | bytes | None | Encryption key for securing tracking data |
| `encoding` | str | "utf-8" | Character encoding for data serialization |
| `append_slash` | bool | False | Whether to append '/' to generated URLs |

### Creating Configurations

```python
from pytracking import Configuration

# Minimal configuration
config = Configuration(
    base_open_tracking_url="https://track.example.com/open/",
    base_click_tracking_url="https://track.example.com/click/"
)

# Full configuration with encryption
from cryptography.fernet import Fernet

key = Fernet.generate_key()
config = Configuration(
    webhook_url="https://api.example.com/tracking-webhook",
    base_open_tracking_url="https://track.example.com/open/",
    base_click_tracking_url="https://track.example.com/click/",
    default_metadata={"source": "email_campaign"},
    include_default_metadata=True,
    encryption_bytestring_key=key,
    append_slash=True
)
```

### Configuration Merging

You can override configuration parameters using kwargs:

```python
# Base configuration
config = Configuration(webhook_url="https://api.example.com/webhook")

# Override parameters for specific use case
open_url = pytracking.get_open_tracking_url(
    metadata={"special": "case"},
    configuration=config,
    webhook_url="https://special.example.com/webhook"  # Overrides config
)
```

---

## API Reference

### Core Functions

#### `get_open_tracking_url(metadata=None, configuration=None, **kwargs)`

Generates a URL for tracking email opens.

**Parameters:**
- `metadata` (dict): Custom data to associate with the tracking event
- `configuration` (Configuration): Configuration object
- `**kwargs`: Configuration parameters that override the configuration object

**Returns:** String URL for open tracking

**Example:**
```python
url = pytracking.get_open_tracking_url(
    metadata={"user_id": 123},
    base_open_tracking_url="https://track.example.com/open/"
)
```

#### `get_click_tracking_url(url_to_track, metadata=None, configuration=None, **kwargs)`

Generates a URL for tracking link clicks.

**Parameters:**
- `url_to_track` (str): The original URL to redirect to after tracking
- `metadata` (dict): Custom data to associate with the tracking event
- `configuration` (Configuration): Configuration object
- `**kwargs`: Configuration parameters

**Returns:** String URL for click tracking

**Example:**
```python
url = pytracking.get_click_tracking_url(
    "https://example.com/product",
    metadata={"product_id": "ABC123"},
    base_click_tracking_url="https://track.example.com/click/"
)
```

#### `get_open_tracking_result(encoded_url_path, request_data=None, configuration=None, **kwargs)`

Decodes an open tracking URL and returns tracking information.

**Parameters:**
- `encoded_url_path` (str): The encoded portion of the tracking URL
- `request_data` (dict): Additional data about the request (user agent, IP, etc.)
- `configuration` (Configuration): Configuration object
- `**kwargs`: Configuration parameters

**Returns:** TrackingResult object

#### `get_click_tracking_result(encoded_url_path, request_data=None, configuration=None, **kwargs)`

Decodes a click tracking URL and returns tracking information.

**Parameters:**
- `encoded_url_path` (str): The encoded portion of the tracking URL
- `request_data` (dict): Additional data about the request
- `configuration` (Configuration): Configuration object
- `**kwargs`: Configuration parameters

**Returns:** TrackingResult object

#### `get_open_tracking_pixel()`

Returns the binary data and MIME type for a 1x1 transparent PNG pixel.

**Returns:** Tuple of (binary_data, mime_type)

**Example:**
```python
pixel_data, mime_type = pytracking.get_open_tracking_pixel()
# pixel_data: binary PNG data
# mime_type: "image/png"
```

### Utility Functions

#### `get_click_tracking_url_path(url, configuration=None, **kwargs)`

Extracts the encoded path from a full click tracking URL.

#### `get_open_tracking_url_path(url, configuration=None, **kwargs)`

Extracts the encoded path from a full open tracking URL.

---

## Features and Usage

### 1. Encryption

Protect tracking data by encrypting it instead of using plain base64 encoding.

```python
from cryptography.fernet import Fernet
import pytracking

# Generate encryption key
key = Fernet.generate_key()

# Create encrypted tracking URL
url = pytracking.get_click_tracking_url(
    "https://example.com/secret-page",
    metadata={"sensitive": "data"},
    base_click_tracking_url="https://track.example.com/click/",
    encryption_bytestring_key=key
)

# Decode encrypted tracking URL
result = pytracking.get_click_tracking_result(
    encoded_path,
    base_click_tracking_url="https://track.example.com/click/",
    encryption_bytestring_key=key
)
```

### 2. Django Integration

PyTracking provides Django views that handle tracking requests automatically.

#### Setup

1. Install with Django support:
```bash
pip install pytracking[django]
```

2. Add configuration to Django settings:
```python
# settings.py
PYTRACKING_CONFIGURATION = {
    "webhook_url": "https://api.example.com/webhook",
    "base_open_tracking_url": "https://mysite.com/tracking/open/",
    "base_click_tracking_url": "https://mysite.com/tracking/click/",
    "default_metadata": {"source": "django_app"},
    "append_slash": True
}
```

3. Create custom views:
```python
# views.py
from pytracking.django import OpenTrackingView, ClickTrackingView
from myapp.tasks import process_tracking_event

class CustomOpenTrackingView(OpenTrackingView):
    def notify_tracking_event(self, tracking_result):
        # Handle the tracking event
        user_id = tracking_result.metadata.get('user_id')
        print(f"Email opened by user {user_id}")
        
        # Send to background task
        process_tracking_event.delay(tracking_result.to_json_dict())
    
    def notify_decoding_error(self, exception, request):
        # Handle decoding errors
        logger.error(f"Tracking decode error: {exception}")

class CustomClickTrackingView(ClickTrackingView):
    def notify_tracking_event(self, tracking_result):
        # Handle the tracking event
        print(f"Link clicked: {tracking_result.tracked_url}")
        process_tracking_event.delay(tracking_result.to_json_dict())
```

4. Configure URLs:
```python
# urls.py
from django.urls import path
from .views import CustomOpenTrackingView, CustomClickTrackingView

urlpatterns = [
    path('tracking/open/<str:path>/', CustomOpenTrackingView.as_view(), name='open_tracking'),
    path('tracking/click/<str:path>/', CustomClickTrackingView.as_view(), name='click_tracking'),
]
```

### 3. HTML Email Processing

Automatically modify HTML emails to add tracking links and pixels.

```python
from pytracking.html import adapt_html

html_email = """
<html>
<body>
    <h1>Newsletter</h1>
    <p>Check out our <a href="https://example.com/product">new product</a>!</p>
    <p>Visit our <a href="https://example.com/blog">blog</a> for more info.</p>
</body>
</html>
"""

# Add tracking to all links and add open tracking pixel
modified_html = adapt_html(
    html_email,
    extra_metadata={"user_id": 123, "campaign": "newsletter"},
    click_tracking=True,
    open_tracking=True,
    base_open_tracking_url="https://track.example.com/open/",
    base_click_tracking_url="https://track.example.com/click/"
)

# The result will have:
# 1. All http/https links replaced with tracking URLs
# 2. A 1x1 pixel added before </body>
```

### 4. Webhook Notifications

Automatically send tracking events to webhooks.

```python
from pytracking.webhook import send_webhook

# When handling a tracking event
tracking_result = pytracking.get_open_tracking_result(encoded_path)

# Send to webhook
response = send_webhook(tracking_result)

# The webhook will receive a JSON POST request:
# {
#     "is_open_tracking": true,
#     "is_click_tracking": false,
#     "metadata": {"user_id": 123},
#     "request_data": {"user_agent": "...", "user_ip": "..."},
#     "timestamp": 1234567890
# }
```

### 5. Metadata Management

Attach custom data to tracking events for analytics and personalization.

```python
# Global default metadata
config = Configuration(
    default_metadata={"source": "newsletter", "version": "v2"},
    include_default_metadata=True
)

# Per-URL metadata
url = pytracking.get_open_tracking_url(
    metadata={"user_id": 123, "segment": "premium"},
    configuration=config
)

# When decoded, metadata will be merged:
# {"source": "newsletter", "version": "v2", "user_id": 123, "segment": "premium"}
```

---

## Advanced Topics

### Custom Encoding Strategies

You can extend PyTracking to use custom encoding methods:

```python
from pytracking.tracking import Configuration
import base64
import json

class CustomConfiguration(Configuration):
    def get_url_encoded_data_str(self, data_to_embed):
        # Custom encoding logic
        json_str = json.dumps(data_to_embed)
        # Apply custom transformation
        custom_encoded = my_custom_encoding(json_str)
        return base64.urlsafe_b64encode(custom_encoded).decode(self.encoding)
```

### Performance Optimization

1. **Use Configuration Objects**: Reuse configuration objects instead of passing parameters as kwargs
2. **Batch Processing**: Process multiple tracking events together
3. **Caching**: Cache frequently used configuration objects
4. **Async Processing**: Use background tasks for webhook notifications

```python
# Good: Reuse configuration
config = Configuration(...)
for user in users:
    url = pytracking.get_open_tracking_url(
        metadata={"user_id": user.id},
        configuration=config
    )

# Avoid: Recreating configuration each time
for user in users:
    url = pytracking.get_open_tracking_url(
        metadata={"user_id": user.id},
        base_open_tracking_url="...",  # Parameters recreate config
        webhook_url="..."
    )
```

### Security Considerations

1. **Use Encryption**: For sensitive metadata, always use encryption
2. **Validate URLs**: Validate tracking URLs before processing
3. **Rate Limiting**: Implement rate limiting on tracking endpoints
4. **HTTPS Only**: Always use HTTPS for tracking URLs
5. **Webhook Security**: Verify webhook authenticity

```python
# Secure configuration
from cryptography.fernet import Fernet

key = Fernet.generate_key()
secure_config = Configuration(
    base_open_tracking_url="https://secure-tracking.example.com/open/",
    base_click_tracking_url="https://secure-tracking.example.com/click/",
    encryption_bytestring_key=key,
    webhook_url="https://secure-webhook.example.com/tracking"
)
```

### Monitoring and Analytics

Track tracking system performance:

```python
import time
from collections import defaultdict

class TrackingAnalytics:
    def __init__(self):
        self.stats = defaultdict(int)
    
    def record_event(self, tracking_result):
        self.stats['total_events'] += 1
        if tracking_result.is_open_tracking:
            self.stats['open_events'] += 1
        if tracking_result.is_click_tracking:
            self.stats['click_events'] += 1
        
        # Record metadata statistics
        for key in tracking_result.metadata:
            self.stats[f'metadata_{key}'] += 1
    
    def get_summary(self):
        return dict(self.stats)

# Usage in Django view
analytics = TrackingAnalytics()

class AnalyticsOpenTrackingView(OpenTrackingView):
    def notify_tracking_event(self, tracking_result):
        analytics.record_event(tracking_result)
        super().notify_tracking_event(tracking_result)
```

---

## Best Practices

### 1. URL Management

- **Keep URLs Short**: Use concise metadata keys
- **Use Meaningful Keys**: Make metadata self-documenting
- **Avoid Sensitive Data**: Don't put passwords/tokens in metadata without encryption

```python
# Good
metadata = {
    "uid": 12345,
    "cmp": "newsletter_2024_01"
}

# Avoid
metadata = {
    "user_identification_number": 12345,
    "campaign_name_with_long_description": "January 2024 Newsletter Campaign"
}
```

### 2. Error Handling

Always handle decoding errors gracefully:

```python
def safe_decode_tracking(encoded_path):
    try:
        return pytracking.get_open_tracking_result(encoded_path, ...)
    except Exception as e:
        logger.error(f"Failed to decode tracking URL: {e}")
        return None
```

### 3. Testing

Test tracking URLs in development:

```python
import pytracking

def test_tracking_roundtrip():
    # Create tracking URL
    original_metadata = {"test": "data"}
    url = pytracking.get_open_tracking_url(
        metadata=original_metadata,
        base_open_tracking_url="https://test.example.com/open/"
    )
    
    # Extract path
    path = pytracking.get_open_tracking_url_path(
        url, 
        base_open_tracking_url="https://test.example.com/open/"
    )
    
    # Decode
    result = pytracking.get_open_tracking_result(
        path,
        base_open_tracking_url="https://test.example.com/open/"
    )
    
    assert result.metadata == original_metadata
    assert result.is_open_tracking == True
```

### 4. Documentation

Document your tracking implementation:

```python
class EmailTracker:
    """
    Handles email tracking for the application.
    
    Supported metadata keys:
    - user_id: ID of the user receiving the email
    - campaign_id: ID of the email campaign
    - template_id: ID of the email template used
    - segment: User segment (premium, basic, etc.)
    """
    
    def __init__(self, config):
        self.config = config
    
    def create_open_pixel(self, user_id, campaign_id):
        """Create an open tracking pixel for email."""
        return pytracking.get_open_tracking_url(
            metadata={
                "user_id": user_id,
                "campaign_id": campaign_id,
                "event_type": "open"
            },
            configuration=self.config
        )
```

---

## Troubleshooting

### Common Issues

#### 1. Decoding Errors

**Problem**: Getting decoding errors when processing tracking URLs.

**Solutions:**
- Verify the encoded path is complete and not truncated
- Check that the same configuration is used for encoding and decoding
- Ensure the correct encryption key is used if encryption is enabled

```python
# Debug decoding issues
try:
    result = pytracking.get_open_tracking_result(encoded_path, ...)
except Exception as e:
    print(f"Decoding error: {e}")
    print(f"Encoded path: {encoded_path}")
    print(f"Path length: {len(encoded_path)}")
```

#### 2. URL Length Issues

**Problem**: Generated URLs are too long.

**Solutions:**
- Use shorter metadata keys
- Enable encryption (can be more efficient than base64)
- Reduce metadata payload size

```python
# Instead of:
metadata = {"user_identification": 123, "campaign_description": "..."}

# Use:
metadata = {"uid": 123, "cmp": "..."}
```

#### 3. Webhook Timeouts

**Problem**: Webhook notifications timing out.

**Solutions:**
- Increase webhook timeout
- Use background tasks for webhook processing
- Implement retry logic

```python
from pytracking.webhook import send_webhook

def send_webhook_with_retry(tracking_result, max_retries=3):
    for attempt in range(max_retries):
        try:
            return send_webhook(tracking_result, webhook_timeout_seconds=10)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

#### 4. Django Integration Issues

**Problem**: Django views not working correctly.

**Solutions:**
- Check URL patterns match the expected format
- Verify `PYTRACKING_CONFIGURATION` is properly set
- Ensure required dependencies are installed

```python
# Verify configuration
from pytracking.django import get_configuration_from_settings

try:
    config = get_configuration_from_settings()
    print(f"Configuration loaded: {config}")
except Exception as e:
    print(f"Configuration error: {e}")
```

### Debugging Tools

#### Enable Detailed Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pytracking')

# Add to your tracking handlers
def debug_tracking_event(tracking_result):
    logger.debug(f"Tracking event: {tracking_result}")
    logger.debug(f"Metadata: {tracking_result.metadata}")
    logger.debug(f"Request data: {tracking_result.request_data}")
```

#### Test URL Generation

```python
def test_url_generation():
    """Test that URLs can be generated and decoded correctly."""
    test_cases = [
        {"metadata": {"simple": "test"}},
        {"metadata": {"unicode": "tést 🚀"}},
        {"metadata": {"complex": {"nested": {"data": [1, 2, 3]}}}},
    ]
    
    for case in test_cases:
        try:
            url = pytracking.get_open_tracking_url(**case, base_open_tracking_url="https://test.com/")
            path = pytracking.get_open_tracking_url_path(url, base_open_tracking_url="https://test.com/")
            result = pytracking.get_open_tracking_result(path, base_open_tracking_url="https://test.com/")
            assert result.metadata == case["metadata"]
            print(f"✓ Test passed: {case}")
        except Exception as e:
            print(f"✗ Test failed: {case} - {e}")
```

---

## Examples

### Complete Email Tracking System

```python
import pytracking
from cryptography.fernet import Fernet
from pytracking.html import adapt_html
from pytracking.webhook import send_webhook

class EmailTrackingSystem:
    def __init__(self):
        # Generate encryption key (store securely in production)
        self.encryption_key = Fernet.generate_key()
        
        self.config = pytracking.Configuration(
            base_open_tracking_url="https://track.myapp.com/open/",
            base_click_tracking_url="https://track.myapp.com/click/",
            webhook_url="https://api.myapp.com/tracking-webhook",
            encryption_bytestring_key=self.encryption_key,
            default_metadata={"app": "myapp", "version": "1.0"}
        )
    
    def prepare_email(self, html_content, recipient_id, campaign_id='cmp01'):
        """Prepare an HTML email with tracking."""
        metadata = {
            "recipient_id": recipient_id,
            "campaign_id": campaign_id,
            "timestamp": int(time.time())
        }
        
        # Add tracking to HTML
        tracked_html = adapt_html(
            html_content,
            extra_metadata=metadata,
            configuration=self.config
        )
        
        return tracked_html
    
    def handle_open_event(self, encoded_path, request_data=None):
        """Handle an email open event."""
        try:
            result = pytracking.get_open_tracking_result(
                encoded_path,
                request_data=request_data,
                configuration=self.config
            )
            
            # Log the event
            print(f"Email opened by recipient {result.metadata.get('recipient_id')}")
            
            # Send webhook notification
            send_webhook(result, configuration=self.config)
            
            # Return tracking pixel
            return pytracking.get_open_tracking_pixel()
            
        except Exception as e:
            print(f"Error handling open event: {e}")
            return None
    
    def handle_click_event(self, encoded_path, request_data=None):
        """Handle a link click event."""
        try:
            result = pytracking.get_click_tracking_result(
                encoded_path,
                request_data=request_data,
                configuration=self.config
            )
            
            # Log the event
            print(f"Link clicked: {result.tracked_url}")
            print(f"Recipient: {result.metadata.get('recipient_id')}")
            
            # Send webhook notification (in background in production)
            send_webhook(result, configuration=self.config)
            
            # Return URL to redirect to
            return result.tracked_url
            
        except Exception as e:
            print(f"Error handling click event: {e}")
            return None

# Usage
tracker = EmailTrackingSystem()

# Prepare email with tracking
html_email = """
<html>
<body>
    <h1>Welcome!</h1>
    <p>Check out our <a href="https://myapp.com/features">new features</a>.</p>
</body>
</html>
"""

tracked_email = tracker.prepare_email(html_email, recipient_id=12345)

# In your web server
def open_tracking_endpoint(request, encoded_path):
    request_data = {
        "user_agent": request.headers.get('User-Agent'),
        "user_ip": request.remote_addr
    }
    
    pixel_data, mime_type = tracker.handle_open_event(encoded_path, request_data)
    
    if pixel_data:
        return Response(pixel_data, mimetype=mime_type)
    else:
        return Response(status=404)

def click_tracking_endpoint(request, encoded_path):
    request_data = {
        "user_agent": request.headers.get('User-Agent'),
        "user_ip": request.remote_addr
    }
    
    redirect_url = tracker.handle_click_event(encoded_path, request_data)
    
    if redirect_url:
        return redirect(redirect_url)
    else:
        return Response(status=404)
```

### Flask Integration Example

```python
from flask import Flask, request, redirect, Response
import pytracking

app = Flask(__name__)

config = pytracking.Configuration(
    base_open_tracking_url="https://myapp.com/track/open/",
    base_click_tracking_url="https://myapp.com/track/click/",
    webhook_url="https://myapp.com/webhook/tracking"
)

@app.route('/track/open/<path:encoded_path>')
def track_open(encoded_path):
    request_data = {
        "user_agent": request.headers.get('User-Agent'),
        "user_ip": request.remote_addr,
        "referrer": request.headers.get('Referer')
    }
    
    try:
        result = pytracking.get_open_tracking_result(
            encoded_path,
            request_data=request_data,
            configuration=config
        )
        
        # Process the tracking event
        process_open_event(result)
        
        # Return tracking pixel
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        return Response(pixel_data, mimetype=mime_type)
        
    except Exception as e:
        app.logger.error(f"Open tracking error: {e}")
        return Response(status=404)

@app.route('/track/click/<path:encoded_path>')
def track_click(encoded_path):
    request_data = {
        "user_agent": request.headers.get('User-Agent'),
        "user_ip": request.remote_addr,
        "referrer": request.headers.get('Referer')
    }
    
    try:
        result = pytracking.get_click_tracking_result(
            encoded_path,
            request_data=request_data,
            configuration=config
        )
        
        # Process the tracking event
        process_click_event(result)
        
        # Redirect to original URL
        return redirect(result.tracked_url)
        
    except Exception as e:
        app.logger.error(f"Click tracking error: {e}")
        return Response(status=404)

def process_open_event(tracking_result):
    """Process email open event."""
    # Store in database, send to analytics, etc.
    print(f"Email opened: {tracking_result.metadata}")

def process_click_event(tracking_result):
    """Process link click event."""
    # Store in database, send to analytics, etc.
    print(f"Link clicked: {tracking_result.tracked_url}")
    print(f"Metadata: {tracking_result.metadata}")

if __name__ == '__main__':
    app.run(debug=True)
```

### Analytics and Reporting

```python
import pytracking
from datetime import datetime, timedelta
from collections import defaultdict

class TrackingAnalytics:
    def __init__(self):
        self.events = []
        self.config = pytracking.Configuration(
            base_open_tracking_url="https://track.example.com/open/",
            base_click_tracking_url="https://track.example.com/click/"
        )
    
    def record_event(self, tracking_result):
        """Record a tracking event for analytics."""
        event_data = {
            "timestamp": datetime.fromtimestamp(tracking_result.timestamp),
            "type": "open" if tracking_result.is_open_tracking else "click",
            "metadata": tracking_result.metadata,
            "request_data": tracking_result.request_data,
            "tracked_url": tracking_result.tracked_url
        }
        self.events.append(event_data)
    
    def get_campaign_stats(self, campaign_id, days=7):
        """Get statistics for a specific campaign."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        campaign_events = [
            event for event in self.events
            if event["metadata"].get("campaign_id") == campaign_id
            and event["timestamp"] >= cutoff_date
        ]
        
        stats = {
            "total_opens": sum(1 for e in campaign_events if e["type"] == "open"),
            "total_clicks": sum(1 for e in campaign_events if e["type"] == "click"),
            "unique_recipients": len(set(
                e["metadata"].get("recipient_id") 
                for e in campaign_events 
                if e["metadata"].get("recipient_id")
            )),
            "top_links": self._get_top_links(campaign_events),
            "engagement_by_day": self._get_engagement_by_day(campaign_events)
        }
        
        return stats
    
    def _get_top_links(self, events):
        """Get most clicked links."""
        link_counts = defaultdict(int)
        for event in events:
            if event["type"] == "click" and event["tracked_url"]:
                link_counts[event["tracked_url"]] += 1
        
        return sorted(link_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _get_engagement_by_day(self, events):
        """Get daily engagement statistics."""
        daily_stats = defaultdict(lambda: {"opens": 0, "clicks": 0})
        
        for event in events:
            day = event["timestamp"].date()
            if event["type"] == "open":
                daily_stats[day]["opens"] += 1
            else:
                daily_stats[day]["clicks"] += 1
        
        return dict(daily_stats)

# Usage
analytics = TrackingAnalytics()

# In your tracking handlers
def handle_tracking_event(tracking_result):
    # Record for analytics
    analytics.record_event(tracking_result)
    
    # Send webhook
    pytracking.webhook.send_webhook(tracking_result)

# Generate reports
campaign_stats = analytics.get_campaign_stats("newsletter_2024_01")
print(f"Campaign opens: {campaign_stats['total_opens']}")
print(f"Campaign clicks: {campaign_stats['total_clicks']}")
print(f"Unique recipients: {campaign_stats['unique_recipients']}")
```

---

## Contributing

### Development Setup

1. Clone the repository
2. Install development dependencies:
```bash
pip install -e .[all,test]
```

3. Run tests:
```bash
tox
```

### Running Tests

PyTracking uses tox for testing across multiple Python versions:

```bash
# Run all tests
tox

# Run tests for specific Python version
tox -e py39-pytracking

# Run Django tests
tox -e py39-django-dj32
```

### Code Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to public functions
- Include type hints where appropriate

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

---

## License

PyTracking is licensed under the New BSD License. See the [LICENSE](LICENSE) file for details.

---

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: This manual and inline documentation
- **Community**: Contribute to the project on GitHub

---

*This manual covers PyTracking version 0.2.3. For the latest updates, visit the [GitHub repository](https://github.com/powergo/pytracking).*
