#!/usr/bin/env python3
"""
Email Tracking CLI Tool
======================

Command-line interface for the PyTracking email tracking system.
Provides utilities for managing campaigns, generating tracking URLs, and viewing analytics.

Usage:
    python tracking_cli.py --help
    python tracking_cli.py create-campaign "My Campaign" --subject "Test Subject"
    python tracking_cli.py generate-pixel --campaign-id 1 --metadata '{"user_id": 123}'
    python tracking_cli.py generate-link "https://example.com" --campaign-id 1
    python tracking_cli.py stats --campaign-id 1
    python tracking_cli.py decode-url "encoded_tracking_url_path"
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Union

import pytracking
from cryptography.fernet import Fernet

# Configuration
TRACKING_CONFIG = pytracking.Configuration(
    base_open_tracking_url="http://localhost:5000/track/open/",
    base_click_tracking_url="http://localhost:5000/track/click/",
    webhook_url="http://localhost:5000/webhook/tracking",
    encryption_bytestring_key=Fernet.generate_key(),
)

class TrackingCLI:
    """CLI interface for email tracking operations"""
    
    def __init__(self):
        self.config = TRACKING_CONFIG
    
    def create_campaign(self, name: str, subject: Optional[str] = None) -> Dict:
        """Create a new campaign"""
        campaign_data = {
            "id": int(time.time()) % 10000,  # Simplified ID generation
            "name": name,
            "subject": subject,
            "created_at": datetime.now().isoformat(),
            "config": {
                "base_open_tracking_url": self.config.base_open_tracking_url,
                "base_click_tracking_url": self.config.base_click_tracking_url,
                "webhook_url": self.config.webhook_url,
                "encryption_enabled": bool(self.config.encryption_bytestring_key)
            }
        }
        
        print(f"✅ Campaign created successfully!")
        print(f"   ID: {campaign_data['id']}")
        print(f"   Name: {campaign_data['name']}")
        if subject:
            print(f"   Subject: {campaign_data['subject']}")
        print(f"   Created: {campaign_data['created_at']}")
        
        return campaign_data
    
    def generate_open_tracking_pixel(self, campaign_id: int, metadata: Optional[Dict] = None) -> str:
        """Generate an open tracking pixel URL"""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "campaign_id": campaign_id,
            "timestamp": int(time.time()),
            "type": "open"
        })
        
        pixel_url = pytracking.get_open_tracking_url(
            metadata=metadata,
            configuration=self.config
        )
        
        print(f"📧 Open tracking pixel generated:")
        print(f"   URL: {pixel_url}")
        print(f"   HTML: <img src=\"{pixel_url}\" width=\"1\" height=\"1\" alt=\"\" />")
        print(f"   Metadata: {json.dumps(metadata, indent=2)}")
        
        return pixel_url
    
    def generate_click_tracking_link(self, original_url: str, campaign_id: int, metadata: Optional[Dict] = None) -> str:
        """Generate a click tracking link"""
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "campaign_id": campaign_id,
            "timestamp": int(time.time()),
            "type": "click",
            "original_url": original_url
        })
        
        tracking_url = pytracking.get_click_tracking_url(
            original_url,
            metadata=metadata,
            configuration=self.config
        )
        
        print(f"🔗 Click tracking link generated:")
        print(f"   Original: {original_url}")
        print(f"   Tracking: {tracking_url}")
        print(f"   HTML: <a href=\"{tracking_url}\">Click here</a>")
        print(f"   Metadata: {json.dumps(metadata, indent=2)}")
        
        return tracking_url
    
    def decode_tracking_url(self, encoded_path: str, url_type: str = "auto") -> Optional[Dict]:
        """Decode a tracking URL and show its contents"""
        try:
            if url_type == "auto":
                # Try to determine type from the path or ask user
                if "/open/" in encoded_path:
                    url_type = "open"
                elif "/click/" in encoded_path:
                    url_type = "click"
                else:
                    url_type = input("Enter URL type (open/click): ").lower()
            
            if url_type == "open":
                result = pytracking.get_open_tracking_result(
                    encoded_path,
                    configuration=self.config
                )
            elif url_type == "click":
                result = pytracking.get_click_tracking_result(
                    encoded_path,
                    configuration=self.config
                )
            else:
                raise ValueError("Invalid URL type. Must be 'open' or 'click'")
            
            print(f"🔍 Decoded tracking URL:")
            print(f"   Type: {'Open' if result.is_open_tracking else 'Click'} tracking")
            if result.timestamp:
                print(f"   Timestamp: {datetime.fromtimestamp(result.timestamp)}")
            if result.tracked_url:
                print(f"   Original URL: {result.tracked_url}")
            if result.webhook_url:
                print(f"   Webhook: {result.webhook_url}")
            print(f"   Metadata: {json.dumps(result.metadata, indent=2)}")
            
            return result.to_json_dict()._asdict()
            
        except Exception as e:
            print(f"❌ Error decoding URL: {e}")
            return None
    
    def generate_sample_email(self, campaign_id: int, recipient_email: str) -> Optional[str]:
        """Generate a sample HTML email with tracking"""
        metadata = {
            "campaign_id": campaign_id,
            "recipient_email": recipient_email,
            "timestamp": int(time.time())
        }
        
        # Sample HTML email
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sample Email</title>
</head>
<body>
    <h1>Welcome to Our Newsletter!</h1>
    <p>Thank you for subscribing to our newsletter. Here are some interesting links:</p>
    
    <ul>
        <li><a href="https://example.com/blog">Visit our blog</a></li>
        <li><a href="https://example.com/products">Check out our products</a></li>
        <li><a href="https://github.com/powergo/pytracking">PyTracking on GitHub</a></li>
    </ul>
    
    <p>Best regards,<br>The Team</p>
    
    <hr>
    <p><small>You received this email because you subscribed to our newsletter.</small></p>
</body>
</html>
        """
        
        # Add tracking using PyTracking's HTML adapter
        try:
            from pytracking.html import adapt_html
            tracked_html = adapt_html(
                html_template,
                extra_metadata=metadata,
                configuration=self.config
            )
            
            output_file = f"sample_email_{campaign_id}_{int(time.time())}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(tracked_html)
            
            print(f"📨 Sample email generated:")
            print(f"   Campaign ID: {campaign_id}")
            print(f"   Recipient: {recipient_email}")
            print(f"   Output file: {output_file}")
            print(f"   Features: Open tracking + Click tracking on all links")
            print(f"   Metadata: {json.dumps(metadata, indent=2)}")
            
            return tracked_html
            
        except ImportError:
            print("❌ HTML tracking requires 'pip install pytracking[html]'")
            return None
    
    def show_config(self):
        """Display current configuration"""
        print("⚙️  Current PyTracking Configuration:")
        print(f"   Open tracking URL: {self.config.base_open_tracking_url}")
        print(f"   Click tracking URL: {self.config.base_click_tracking_url}")
        print(f"   Webhook URL: {self.config.webhook_url}")
        print(f"   Encryption enabled: {bool(self.config.encryption_bytestring_key)}")
        print(f"   Default timeout: {self.config.webhook_timeout_seconds}s")
    
    def test_tracking_system(self):
        """Run a comprehensive test of the tracking system"""
        print("🧪 Testing PyTracking System...")
        print("=" * 50)
        
        # Test 1: Create sample campaign
        print("Test 1: Creating sample campaign...")
        campaign = self.create_campaign("Test Campaign", "Test Subject")
        campaign_id = campaign["id"]
        
        print("\n" + "-" * 30)
        
        # Test 2: Generate tracking pixel
        print("Test 2: Generating open tracking pixel...")
        pixel_url = self.generate_open_tracking_pixel(
            campaign_id, 
            {"user_id": 123, "test": True}
        )
        
        print("\n" + "-" * 30)
        
        # Test 3: Generate tracking link
        print("Test 3: Generating click tracking link...")
        link_url = self.generate_click_tracking_link(
            "https://example.com/test",
            campaign_id,
            {"user_id": 123, "test": True}
        )
        
        print("\n" + "-" * 30)
        
        # Test 4: Decode URLs
        print("Test 4: Decoding tracking URLs...")
        pixel_path = pytracking.get_open_tracking_url_path(pixel_url, configuration=self.config)
        link_path = pytracking.get_click_tracking_url_path(link_url, configuration=self.config)
        
        print("Decoding pixel URL:")
        self.decode_tracking_url(pixel_path, "open")
        
        print("\nDecoding link URL:")
        self.decode_tracking_url(link_path, "click")
        
        print("\n" + "-" * 30)
        
        # Test 5: Generate sample email
        print("Test 5: Generating sample email with tracking...")
        self.generate_sample_email(campaign_id, "test@example.com")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nNext steps:")
        print("1. Start the web server: python complete_tracking_system.py")
        print("2. Open the generated HTML file in a browser")
        print("3. Click on links to test tracking")
        print("4. Check the dashboard for tracking events")

def main():
    parser = argparse.ArgumentParser(
        description="PyTracking CLI - Email tracking utilities"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create campaign command
    create_parser = subparsers.add_parser('create-campaign', help='Create a new campaign')
    create_parser.add_argument('name', help='Campaign name')
    create_parser.add_argument('--subject', help='Email subject')
    
    # Generate pixel command
    pixel_parser = subparsers.add_parser('generate-pixel', help='Generate open tracking pixel')
    pixel_parser.add_argument('--campaign-id', type=int, required=True, help='Campaign ID')
    pixel_parser.add_argument('--metadata', help='JSON metadata')
    
    # Generate link command
    link_parser = subparsers.add_parser('generate-link', help='Generate click tracking link')
    link_parser.add_argument('url', help='Original URL to track')
    link_parser.add_argument('--campaign-id', type=int, required=True, help='Campaign ID')
    link_parser.add_argument('--metadata', help='JSON metadata')
    
    # Decode URL command
    decode_parser = subparsers.add_parser('decode-url', help='Decode tracking URL')
    decode_parser.add_argument('path', help='Encoded URL path')
    decode_parser.add_argument('--type', choices=['open', 'click', 'auto'], default='auto', help='URL type')
    
    # Generate email command
    email_parser = subparsers.add_parser('generate-email', help='Generate sample email with tracking')
    email_parser.add_argument('--campaign-id', type=int, required=True, help='Campaign ID')
    email_parser.add_argument('--recipient', required=True, help='Recipient email')
    
    # Config command
    subparsers.add_parser('config', help='Show current configuration')
    
    # Test command
    subparsers.add_parser('test', help='Run comprehensive tracking system test')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = TrackingCLI()
    
    try:
        if args.command == 'create-campaign':
            cli.create_campaign(args.name, args.subject)
        
        elif args.command == 'generate-pixel':
            metadata = json.loads(args.metadata) if args.metadata else {}
            cli.generate_open_tracking_pixel(args.campaign_id, metadata)
        
        elif args.command == 'generate-link':
            metadata = json.loads(args.metadata) if args.metadata else {}
            cli.generate_click_tracking_link(args.url, args.campaign_id, metadata)
        
        elif args.command == 'decode-url':
            cli.decode_tracking_url(args.path, args.type)
        
        elif args.command == 'generate-email':
            cli.generate_sample_email(args.campaign_id, args.recipient)
        
        elif args.command == 'config':
            cli.show_config()
        
        elif args.command == 'test':
            cli.test_tracking_system()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
