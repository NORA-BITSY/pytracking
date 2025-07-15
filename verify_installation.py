#!/usr/bin/env python3
"""
PyTracking Installation Verification Script

This script verifies that PyTracking is properly installed and working.
Run this script after installation to ensure everything is set up correctly.

Usage:
    python verify_installation.py
"""

import sys
import traceback

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n📋 {title}")
    print('-' * 50)

def check_python_version():
    """Check if Python version is compatible."""
    print_section("Python Version Check")
    
    if sys.version_info < (3, 6):
        print("❌ FAILED: Python 3.6+ required")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ PASSED: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_pytracking_import():
    """Check if pytracking can be imported."""
    print_section("PyTracking Import Check")
    
    try:
        import pytracking
        print("✅ PASSED: PyTracking imported successfully")
        
        # Try to access main classes
        config = pytracking.Configuration()
        print("✅ PASSED: Configuration class accessible")
        
        return True
    except ImportError as e:
        print("❌ FAILED: Cannot import pytracking")
        print(f"   Error: {e}")
        print("   Solution: Run 'pip install pytracking'")
        return False
    except Exception as e:
        print("❌ FAILED: Error accessing pytracking components")
        print(f"   Error: {e}")
        return False

def check_optional_features():
    """Check which optional features are available."""
    print_section("Optional Features Check")
    
    features = {
        'Django Integration': {
            'module': 'pytracking.django',
            'install': 'pip install pytracking[django]',
            'deps': ['django', 'django_ipware']
        },
        'HTML Processing': {
            'module': 'pytracking.html',
            'install': 'pip install pytracking[html]',
            'deps': ['lxml']
        },
        'Webhook Support': {
            'module': 'pytracking.webhook',
            'install': 'pip install pytracking[webhook]',
            'deps': ['requests']
        },
        'Encryption': {
            'module': 'cryptography.fernet',
            'install': 'pip install pytracking[crypto]',
            'deps': ['cryptography']
        }
    }
    
    available_features = []
    
    for feature_name, info in features.items():
        try:
            __import__(info['module'])
            print(f"✅ {feature_name}: Available")
            available_features.append(feature_name)
        except ImportError:
            print(f"ℹ️  {feature_name}: Not installed (optional)")
            print(f"   Install with: {info['install']}")
    
    if not available_features:
        print("\nℹ️  No optional features installed. Install with:")
        print("   pip install pytracking[all]  # All features")
    
    return available_features

def test_basic_functionality():
    """Test basic tracking functionality."""
    print_section("Basic Functionality Test")
    
    try:
        import pytracking
        
        # Test configuration
        config = pytracking.Configuration(
            base_open_tracking_url="https://example.com/track/open/",
            base_click_tracking_url="https://example.com/track/click/"
        )
        print("✅ Configuration creation: PASSED")
        
        # Test open tracking URL generation
        open_url = pytracking.get_open_tracking_url(
            configuration=config,
            metadata={"test_user": "123", "test_campaign": "verification"}
        )
        
        if open_url and open_url.startswith("https://example.com/track/open/"):
            print("✅ Open tracking URL generation: PASSED")
        else:
            print("❌ Open tracking URL generation: FAILED")
            return False
        
        # Test click tracking URL generation
        click_url = pytracking.get_click_tracking_url(
            "https://example.com/target",
            configuration=config,
            metadata={"test_user": "123", "test_link": "verification"}
        )
        
        if click_url and click_url.startswith("https://example.com/track/click/"):
            print("✅ Click tracking URL generation: PASSED")
        else:
            print("❌ Click tracking URL generation: FAILED")
            return False
        
        # Test URL decoding (round-trip test)
        try:
            # Extract the path from the open tracking URL
            from urllib.parse import urlparse
            parsed_url = urlparse(open_url)
            
            # Get the encoded path part
            encoded_path = pytracking.get_open_tracking_url_path(
                open_url, configuration=config
            )
            
            # Decode the tracking data
            result = pytracking.get_open_tracking_result(
                encoded_path,
                configuration=config
            )
            
            if result and result.metadata.get("test_user") == "123":
                print("✅ URL encoding/decoding: PASSED")
            else:
                print("❌ URL encoding/decoding: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ URL encoding/decoding: FAILED ({e})")
            return False
        
        # Test tracking pixel
        pixel_data, mime_type = pytracking.get_open_tracking_pixel()
        if pixel_data and mime_type == "image/png":
            print("✅ Tracking pixel generation: PASSED")
        else:
            print("❌ Tracking pixel generation: FAILED")
            return False
        
        print("\n🎉 All basic functionality tests PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test FAILED: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        return False

def test_encryption_feature():
    """Test encryption functionality if available."""
    print_section("Encryption Feature Test")
    
    try:
        from cryptography.fernet import Fernet
        import pytracking
        
        # Generate encryption key
        key = Fernet.generate_key()
        
        # Test encrypted configuration
        config = pytracking.Configuration(
            base_open_tracking_url="https://example.com/track/open/",
            encryption_bytestring_key=key
        )
        
        # Generate encrypted URL
        encrypted_url = pytracking.get_open_tracking_url(
            configuration=config,
            metadata={"sensitive": "data", "user_id": "encrypted_test"}
        )
        
        # Test decoding
        from urllib.parse import urlparse
        parsed_url = urlparse(encrypted_url)
        encoded_path = pytracking.get_open_tracking_url_path(
            encrypted_url, configuration=config
        )
        result = pytracking.get_open_tracking_result(
            encoded_path,
            configuration=config
        )
        
        if result and result.metadata.get("user_id") == "encrypted_test":
            print("✅ Encryption functionality: PASSED")
            return True
        else:
            print("❌ Encryption functionality: FAILED (decoding failed)")
            return False
            
    except ImportError:
        print("ℹ️  Encryption not available (install with: pip install pytracking[crypto])")
        return None
    except Exception as e:
        print(f"❌ Encryption test FAILED: {e}")
        return False

def show_sample_usage():
    """Show sample usage examples."""
    print_section("Sample Usage Examples")
    
    print("Here are some sample code snippets to get you started:\n")
    
    print("1. Basic Configuration:")
    print("""
import pytracking

config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    base_click_tracking_url="https://yourdomain.com/track/click/"
)
""")
    
    print("2. Generate Tracking URLs:")
    print("""
# Open tracking (email pixel)
open_url = pytracking.get_open_tracking_url(
    configuration=config,
    metadata={"user_id": "123", "campaign_id": "summer2023"}
)

# Click tracking (link redirect)
click_url = pytracking.get_click_tracking_url(
    "https://yourdomain.com/products",
    configuration=config,
    metadata={"user_id": "123", "link_type": "product"}
)
""")
    
    print("3. Process Tracking Requests:")
    print("""
# In your web server, handle tracking requests
def handle_open_tracking(request_path):
    result = pytracking.get_open_tracking_result(
        tracking_url_path=request_path,
        configuration=config
    )
    if result:
        print(f"Email opened by user: {result.metadata}")
        # Return tracking pixel
        return pytracking.get_open_tracking_pixel()
""")

def show_next_steps():
    """Show next steps for users."""
    print_section("Next Steps")
    
    print("🎯 Now that PyTracking is working, here's what you can do next:")
    print()
    print("1. 📖 Read the User Guide:")
    print("   - Open USER_GUIDE.md for detailed documentation")
    print("   - Learn about advanced features and integrations")
    print()
    print("2. 🔧 Set up your tracking endpoints:")
    print("   - Create web endpoints to handle /track/open/ and /track/click/")
    print("   - See Django integration examples in the User Guide")
    print()
    print("3. 🔐 Consider security features:")
    print("   - Install encryption: pip install pytracking[crypto]")
    print("   - Use HTTPS for all tracking URLs")
    print()
    print("4. 📧 Test with real emails:")
    print("   - Send test emails with tracking")
    print("   - Verify tracking works across different email clients")
    print()
    print("5. 📊 Set up analytics:")
    print("   - Implement webhook handlers")
    print("   - Store tracking data in your database")

def main():
    """Run all verification checks."""
    print_header("PyTracking Installation Verification")
    print("This script will verify your PyTracking installation is working correctly.")
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("PyTracking Import", check_pytracking_import),
        ("Optional Features", check_optional_features),
        ("Basic Functionality", test_basic_functionality),
        ("Encryption Feature", test_encryption_feature),
    ]
    
    results = []
    critical_checks = 4  # First 4 checks are critical
    
    for i, (check_name, check_func) in enumerate(checks):
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results.append(False)
        
        # Show progress
        if i < len(checks) - 1:
            print()  # Add spacing between checks
    
    # Summary
    print_header("Verification Summary")
    
    critical_results = results[:critical_checks]
    critical_passed = sum(1 for r in critical_results if r is True)
    
    if all(r is not False for r in critical_results):
        print("🎉 SUCCESS: PyTracking is properly installed and working!")
        print(f"✅ {critical_passed}/{critical_checks} critical checks passed")
        
        optional_results = results[critical_checks:]
        optional_passed = sum(1 for r in optional_results if r is True)
        optional_available = sum(1 for r in optional_results if r is not None)
        
        if optional_available > 0:
            print(f"✅ {optional_passed}/{optional_available} optional features working")
        
        show_sample_usage()
        show_next_steps()
        
    else:
        print("❌ FAILED: PyTracking installation has issues")
        failed_checks = [
            checks[i][0] for i, result in enumerate(critical_results) 
            if result is False
        ]
        print(f"Failed checks: {', '.join(failed_checks)}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Make sure you have Python 3.6+ installed")
        print("2. Install PyTracking: pip install pytracking")
        print("3. Check for installation errors above")
        print("4. See INSTALLATION_GUIDE.md for detailed troubleshooting")
        
        return 1  # Exit with error code
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
