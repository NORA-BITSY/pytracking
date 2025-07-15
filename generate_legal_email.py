#!/usr/bin/env python3
"""
Generate Legal Correspondence Email with Open Tracking
This script creates a tracked version of the legal correspondence email.
"""

import pytracking
from cryptography.fernet import Fernet
import os
from datetime import datetime

def create_legal_correspondence_email():
    """Create the legal correspondence email with tracking."""
    
    # Generate encryption key for secure tracking
    encryption_key = Fernet.generate_key()
    print(f"🔐 Generated encryption key: {encryption_key.decode()}")
    print("📝 Store this key securely for decoding tracking data")
    
    # Configure PyTracking
    config = pytracking.Configuration(
        base_open_tracking_url="https://realproductpat.com/track/open/",
        base_click_tracking_url="https://realproductpat.com/track/click/",
        webhook_url="https://realproductpat.com/webhooks/legal-tracking/",
        encryption_bytestring_key=encryption_key,
        default_metadata={
            "source": "legal_correspondence",
            "document_type": "discovery_demand",
            "case_number": "2025CF000089"
        }
    )
    
    # Email metadata for tracking
    metadata = {
        "recipient": "matthew.kirkpatrick@piercecounty.gov",
        "sender": "james.patrick.white@example.com",
        "document_id": "legal_001",
        "case_name": "State v. White",
        "case_number": "2025CF000089",
        "document_type": "discovery_correspondence",
        "date_created": datetime.now().isoformat(),
        "priority": "urgent",
        "deadline": "72_hours",
        "legal_category": "discovery_demand",
        "subject_matter": "toxicology_evidence_challenge"
    }
    
    # Generate tracking URL
    tracking_url = pytracking.get_open_tracking_url(
        configuration=config,
        metadata=metadata
    )
    
    print(f"📧 Generated tracking URL: {tracking_url}")
    print(f"📊 Tracking metadata: {metadata}")
    
    # Read the HTML template
    with open("legal_correspondence.html", "r") as f:
        html_content = f.read()
    
    # Replace placeholder with actual tracking URL
    tracked_html = html_content.replace("TRACKING_URL_PLACEHOLDER", tracking_url)
    
    # Save the tracked email
    output_filename = "legal_correspondence_tracked.html"
    with open(output_filename, "w") as f:
        f.write(tracked_html)
    
    print(f"✅ Created tracked email: {output_filename}")
    
    # Create a summary file with tracking information
    summary_filename = "legal_tracking_info.txt"
    with open(summary_filename, "w") as f:
        f.write("LEGAL CORRESPONDENCE TRACKING INFORMATION\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Date Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Case Number: 2025CF000089\n")
        f.write(f"Document Type: Discovery Correspondence\n\n")
        f.write(f"Encryption Key: {encryption_key.decode()}\n")
        f.write(f"Tracking URL: {tracking_url}\n\n")
        f.write("METADATA:\n")
        for key, value in metadata.items():
            f.write(f"  {key}: {value}\n")
        f.write(f"\nWebhook URL: {config.webhook_url}\n")
        f.write(f"Open Tracking URL: {config.base_open_tracking_url}\n")
        f.write(f"Click Tracking URL: {config.base_click_tracking_url}\n")
    
    print(f"📄 Created tracking info: {summary_filename}")
    
    return {
        "html_file": output_filename,
        "tracking_url": tracking_url,
        "encryption_key": encryption_key.decode(),
        "metadata": metadata,
        "config": config
    }

def decode_tracking_example(tracking_url, encryption_key_str, config):
    """Example of how to decode tracking data when email is opened."""
    
    print("\n" + "=" * 60)
    print("EXAMPLE: How to decode tracking data when email is opened")
    print("=" * 60)
    
    try:
        # Extract the encoded path from the URL
        encoded_path = pytracking.get_open_tracking_url_path(
            tracking_url, 
            configuration=config
        )
        
        # Decode the tracking result
        result = pytracking.get_open_tracking_result(
            encoded_path,
            configuration=config,
            request_data={
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "user_ip": "192.168.1.100",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        print(f"✅ Successfully decoded tracking data:")
        print(f"   Recipient: {result.metadata.get('recipient')}")
        print(f"   Case Number: {result.metadata.get('case_number')}")
        print(f"   Document Type: {result.metadata.get('document_type')}")
        print(f"   Priority: {result.metadata.get('priority')}")
        print(f"   Legal Category: {result.metadata.get('legal_category')}")
        print(f"   Webhook URL: {result.webhook_url}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error decoding tracking data: {e}")
        return None

if __name__ == "__main__":
    print("🏛️  LEGAL CORRESPONDENCE EMAIL TRACKING GENERATOR")
    print("=" * 60)
    
    # Generate the tracked email
    result = create_legal_correspondence_email()
    
    # Show example of decoding
    decode_tracking_example(
        result["tracking_url"], 
        result["encryption_key"],
        result["config"]
    )
    
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    print("=" * 60)
    print("1. 📧 Send the tracked email: legal_correspondence_tracked.html")
    print("2. 🔗 Set up webhook handler at: https://realproductpat.com/webhooks/legal-tracking/")
    print("3. 📊 Monitor tracking data when email is opened")
    print("4. 🔐 Keep encryption key secure: legal_tracking_info.txt")
    print("5. ⚖️  Use tracking data for legal documentation if needed")
    
    print(f"\n🎯 When the email is opened, the tracking pixel will send data to:")
    print(f"   {result['config'].webhook_url}")
