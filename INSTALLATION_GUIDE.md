# PyTracking Installation & Setup Guide

## Table of Contents
- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Optional Dependencies](#optional-dependencies)
- [Environment Setup](#environment-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Overview

PyTracking is a Python library that provides email open and click tracking functionality. It allows you to:
- Track when recipients open your emails using transparent tracking pixels
- Track when recipients click links in your emails
- Encode tracking metadata directly in URLs (stateless approach)
- Optionally encrypt tracking data for security
- Integrate with Django applications
- Send tracking data to webhooks

## System Requirements

### Python Version
- **Python 3.6 or higher** (3.6, 3.7, 3.8, 3.9+ supported)
- **Not compatible with Python 2.x**

### Operating Systems
- Linux (all distributions)
- macOS
- Windows

### Memory & Storage
- Minimal requirements: ~10MB disk space
- Runtime memory: <5MB for basic usage

## Installation Methods

**⚠️ Important for macOS/zsh users:** When installing packages with extras (features in square brackets), you need to quote the package name to avoid shell interpretation issues:

```bash
# ✅ Correct for zsh (macOS default since Catalina)
pip install 'pytracking[all]'

# ❌ Will fail in zsh
pip install pytracking[all]  # Error: zsh: no matches found
```

### Method 1: Basic Installation (Recommended for beginners)

Install the core library without optional features:

```bash
pip install pytracking
```

This provides basic open and click tracking functionality.

### Method 2: Installation with Specific Features

Install with specific optional features you need:

**Note for zsh users (macOS default):** Use quotes around package names with brackets:

```bash
# For Django integration
pip install 'pytracking[django]'

# For encryption support
pip install 'pytracking[crypto]'

# For HTML email modification
pip install 'pytracking[html]'

# For webhook support
pip install 'pytracking[webhook]'

# Multiple features
pip install 'pytracking[django,crypto,webhook]'
```

**For bash users:**
```bash
# These work without quotes in bash
pip install pytracking[django]
pip install pytracking[crypto]
pip install pytracking[html]
pip install pytracking[webhook]
pip install pytracking[django,crypto,webhook]
```

### Method 3: Complete Installation (All Features)

Install with all optional features:

```bash
# For zsh users (macOS default)
pip install 'pytracking[all]'

# For bash users  
pip install pytracking[all]
```

### Method 4: Development Installation

For development or contributing to the project:

```bash
# Clone the repository
git clone https://github.com/powergo/pytracking.git
cd pytracking

# Install in development mode
pip install -e .

# Install with all features for development
pip install -e '.[all,test]'
```

## Optional Dependencies

### Core Features (Always Available)
- Basic open tracking
- Basic click tracking  
- URL encoding/decoding
- Base64 encoding

### Django Integration (`pip install pytracking[django]`)
**Dependencies:** `django>=1.11`, `django-ipware>=2.0.0`

**Features:**
- Django views for handling tracking URLs
- Automatic request data extraction (IP, User-Agent)
- Django-specific helpers

### Encryption Support (`pip install pytracking[crypto]`)
**Dependencies:** `cryptography>=1.4`

**Features:**
- Encrypt tracking data in URLs
- Secure tracking information from tampering
- Fernet encryption support

### HTML Email Modification (`pip install pytracking[html]`)
**Dependencies:** `lxml>=3.6.1`

**Features:**
- Automatically modify HTML emails
- Replace all links with tracking links
- Add tracking pixels to emails

### Webhook Support (`pip install pytracking[webhook]`)
**Dependencies:** `requests>=2.10.0`

**Features:**
- Send tracking data to webhooks
- HTTP POST requests with tracking information
- Configurable timeout settings

### Testing (`pip install pytracking[test]`)
**Dependencies:** `tox>=2.3.1`, `pytest>=2.9.2`

**Features:**
- Run the test suite
- Development testing tools

## Environment Setup

### Virtual Environment (Recommended)

Create an isolated Python environment:

```bash
# Using venv (Python 3.6+)
python -m venv pytracking-env
source pytracking-env/bin/activate  # On Windows: pytracking-env\Scripts\activate

# Install pytracking
pip install 'pytracking[all]'
```

### Using conda

```bash
# Create conda environment
conda create -n pytracking python=3.8
conda activate pytracking

# Install pytracking
pip install 'pytracking[all]'
```

### Docker Setup

Create a `Dockerfile` for containerized usage:

```dockerfile
FROM python:3.8-slim

# Install pytracking with all features
RUN pip install 'pytracking[all]'

# Copy your application code
COPY . /app
WORKDIR /app

# Your application setup here
CMD ["python", "your_app.py"]
```

## Verification

### Basic Installation Check

```python
# test_installation.py
import pytracking

# Check version
print(f"PyTracking version: {pytracking.__version__ if hasattr(pytracking, '__version__') else 'Unknown'}")

# Test basic functionality
config = pytracking.Configuration(
    base_open_tracking_url="https://example.com/track/open/",
    base_click_tracking_url="https://example.com/track/click/"
)

# Generate a simple tracking URL
tracking_url = pytracking.get_open_tracking_url(
    configuration=config,
    metadata={"user_id": "123", "email_id": "456"}
)

print(f"Sample tracking URL: {tracking_url}")
print("✅ Basic installation successful!")
```

### Feature-Specific Tests

#### Test Encryption (if installed)
```python
try:
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    print("✅ Encryption support available")
except ImportError:
    print("❌ Encryption support not installed")
```

#### Test Django Integration (if installed)
```python
try:
    import pytracking.django
    print("✅ Django integration available")
except ImportError:
    print("❌ Django integration not installed")
```

#### Test HTML Processing (if installed)
```python
try:
    import pytracking.html
    print("✅ HTML processing available")
except ImportError:
    print("❌ HTML processing not installed")
```

#### Test Webhook Support (if installed)
```python
try:
    import pytracking.webhook
    print("✅ Webhook support available")
except ImportError:
    print("❌ Webhook support not installed")
```

### Complete Verification Script

```python
#!/usr/bin/env python
"""
PyTracking Installation Verification Script
Run this script to verify your installation is working correctly.
"""

import sys

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required. Current version:", sys.version)
        return False
    else:
        print(f"✅ Python version: {sys.version}")
        return True

def check_pytracking_import():
    """Check if pytracking can be imported."""
    try:
        import pytracking
        print("✅ PyTracking imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import pytracking: {e}")
        return False

def check_optional_features():
    """Check which optional features are available."""
    features = {
        'Django': 'pytracking.django',
        'HTML': 'pytracking.html', 
        'Webhook': 'pytracking.webhook',
        'Crypto': 'cryptography.fernet'
    }
    
    available_features = []
    for feature_name, module_name in features.items():
        try:
            __import__(module_name)
            print(f"✅ {feature_name} support available")
            available_features.append(feature_name)
        except ImportError:
            print(f"ℹ️  {feature_name} support not installed (optional)")
    
    return available_features

def test_basic_functionality():
    """Test basic tracking functionality."""
    try:
        import pytracking
        
        config = pytracking.Configuration(
            base_open_tracking_url="https://example.com/track/open/",
            base_click_tracking_url="https://example.com/track/click/"
        )
        
        # Test open tracking
        open_url = pytracking.get_open_tracking_url(
            configuration=config,
            metadata={"test": "value"}
        )
        
        # Test click tracking
        click_url = pytracking.get_click_tracking_url(
            "https://example.com/target",
            configuration=config,
            metadata={"test": "value"}
        )
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("🔍 PyTracking Installation Verification\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("PyTracking Import", check_pytracking_import),
        ("Optional Features", check_optional_features),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        result = check_func()
        results.append(result)
    
    print(f"\n{'='*50}")
    if all(results[:3]):  # First 3 checks are critical
        print("🎉 Installation verification completed successfully!")
        print("PyTracking is ready to use.")
    else:
        print("⚠️  Installation verification found issues.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Common Installation Issues

#### Issue: `zsh: no matches found: pytracking[all]` (macOS zsh users)
**Symptoms:** Error when using square brackets in package names
**Solutions:**
1. Use quotes around the package name: `pip install 'pytracking[all]'`
2. Escape the brackets: `pip install pytracking\[all\]`
3. Use the full python path if pip is not in PATH: `/path/to/python -m pip install 'pytracking[all]'`

Example fix for your situation:
```bash
# Instead of: pip install pytracking[all]
# Use this:
pip install 'pytracking[all]'

# Or if pip is not found, use your virtual environment python:
/Users/productpat/Library/CloudStorage/Dropbox/pytracking/.venv/bin/python -m pip install 'pytracking[all]'
```

#### Issue: `zsh: command not found: pip`
**Solutions:**
1. Use the full path to pip: `/path/to/your/venv/bin/pip install pytracking`
2. Use python -m pip: `python -m pip install pytracking`
3. Activate your virtual environment first: `source /path/to/venv/bin/activate`

#### Issue: `pip install pytracking` fails
**Solutions:**
1. Upgrade pip: `pip install --upgrade pip`
2. Use Python 3 explicitly: `python3 -m pip install pytracking`
3. Try with `--user` flag: `pip install --user pytracking`

#### Issue: Import errors after installation
**Solutions:**
1. Check if you're in the correct virtual environment
2. Verify Python path: `python -c "import sys; print(sys.path)"`
3. Reinstall: `pip uninstall pytracking && pip install pytracking`

#### Issue: Optional features not working
**Symptoms:** ImportError when using Django, encryption, etc.
**Solutions:**
1. Install specific features: `pip install 'pytracking[django]'`
2. Check installed packages: `pip list | grep pytracking`
3. Install all features: `pip install 'pytracking[all]'`

#### Issue: cryptography installation fails
**Common on:** Older systems, Alpine Linux
**Solutions:**
```bash
# On Ubuntu/Debian
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

# On CentOS/RHEL
sudo yum install gcc openssl-devel libffi-devel python3-devel

# On Alpine Linux
apk add gcc musl-dev libffi-dev openssl-dev python3-dev

# Then retry installation
pip install 'pytracking[crypto]'
```

#### Issue: lxml installation fails
**Solutions:**
```bash
# On Ubuntu/Debian
sudo apt-get install libxml2-dev libxslt-dev python3-dev

# On CentOS/RHEL  
sudo yum install libxml2-devel libxslt-devel python3-devel

# On macOS
brew install libxml2 libxslt

# Then retry installation
pip install 'pytracking[html]'
```

### Platform-Specific Notes

#### Windows
- Use `py -m pip` instead of `pip` if you have multiple Python versions
- Install Microsoft Visual C++ Build Tools for native extensions
- Consider using WSL for easier dependency management

#### macOS
- Install Xcode Command Line Tools: `xcode-select --install`
- Use Homebrew for system dependencies
- Consider using pyenv for Python version management

#### Linux
- Install development packages for your distribution
- Use distribution package manager for system dependencies
- Consider using pyenv or conda for Python management

### Getting Help

If you encounter issues not covered here:

1. **Check the GitHub Issues:** https://github.com/powergo/pytracking/issues
2. **Documentation:** Read the full README.rst for detailed usage
3. **Create an Issue:** Provide:
   - Python version (`python --version`)
   - Operating system
   - Installation command used
   - Complete error message
   - Output of `pip list`

### Next Steps

After successful installation, proceed to the [User Guide](USER_GUIDE.md) to learn how to use PyTracking in your applications.
