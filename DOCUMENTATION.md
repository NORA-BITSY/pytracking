# PyTracking Documentation

This repository contains comprehensive documentation for the PyTracking email open and click tracking library.

## 📚 Documentation

### 🚀 [Installation Guide](INSTALLATION_GUIDE.md)
Complete installation setup instructions including:
- System requirements and compatibility
- Step-by-step installation methods
- Optional feature dependencies
- Environment setup (virtual environments, Docker)
- Installation verification and troubleshooting
- Platform-specific notes and common issues

### 📖 [User Guide](USER_GUIDE.md)  
Comprehensive usage documentation covering:
- Quick start examples
- Core concepts and tracking types
- Configuration options and best practices
- Open tracking implementation
- Click tracking implementation
- HTML email processing
- Encryption and security
- Django integration
- Webhook integration
- Advanced usage patterns
- Complete API reference

## 🔗 Quick Links

| Topic | Installation Guide | User Guide |
|-------|-------------------|------------|
| **Getting Started** | [Installation Methods](INSTALLATION_GUIDE.md#installation-methods) | [Quick Start](USER_GUIDE.md#quick-start) |
| **Features** | [Optional Dependencies](INSTALLATION_GUIDE.md#optional-dependencies) | [Core Concepts](USER_GUIDE.md#core-concepts) |
| **Django** | [Django Setup](INSTALLATION_GUIDE.md#optional-dependencies) | [Django Integration](USER_GUIDE.md#django-integration) |
| **Security** | [Encryption Install](INSTALLATION_GUIDE.md#encryption-support-pip-install-pytrackingcrypto) | [Encryption Usage](USER_GUIDE.md#encryption) |
| **Troubleshooting** | [Common Issues](INSTALLATION_GUIDE.md#troubleshooting) | [Best Practices](USER_GUIDE.md#best-practices) |

## 🎯 Choose Your Path

### New to PyTracking?
1. Start with the [Installation Guide](INSTALLATION_GUIDE.md) to set up the library
2. Run the verification script to ensure everything works
3. Follow the [Quick Start](USER_GUIDE.md#quick-start) in the User Guide
4. Explore specific features as needed

### Experienced Developer?
- Jump directly to the [User Guide](USER_GUIDE.md) for implementation details
- Check the [API Reference](USER_GUIDE.md#api-reference) for complete function documentation
- Review [Best Practices](USER_GUIDE.md#best-practices) for production usage

### Need Help?
- Check [Troubleshooting](INSTALLATION_GUIDE.md#troubleshooting) for common issues
- Review the [GitHub Issues](https://github.com/powergo/pytracking/issues)
- See the original [README.rst](README.rst) for library overview

## 📋 Feature Matrix

| Feature | Installation Required | Documentation |
|---------|----------------------|---------------|
| **Basic Tracking** | `pip install pytracking` | [Open](USER_GUIDE.md#open-tracking) & [Click](USER_GUIDE.md#click-tracking) Tracking |
| **Django Integration** | `pip install pytracking[django]` | [Django Integration](USER_GUIDE.md#django-integration) |
| **Encryption** | `pip install pytracking[crypto]` | [Encryption](USER_GUIDE.md#encryption) |
| **HTML Processing** | `pip install pytracking[html]` | [HTML Email Processing](USER_GUIDE.md#html-email-processing) |
| **Webhooks** | `pip install pytracking[webhook]` | [Webhook Integration](USER_GUIDE.md#webhook-integration) |
| **All Features** | `pip install pytracking[all]` | [Complete Guide](USER_GUIDE.md) |

## 💡 Examples

### Basic Usage
```python
import pytracking

# Configure tracking
config = pytracking.Configuration(
    base_open_tracking_url="https://yourdomain.com/track/open/",
    base_click_tracking_url="https://yourdomain.com/track/click/"
)

# Generate tracking URLs
open_url = pytracking.get_open_tracking_url(
    configuration=config,
    metadata={"user_id": "123", "campaign_id": "summer2023"}
)

click_url = pytracking.get_click_tracking_url(
    "https://yourdomain.com/products",
    configuration=config,
    metadata={"user_id": "123", "link_type": "product"}
)
```

For more examples, see the [User Guide](USER_GUIDE.md#quick-start).

---

*These guides complement the original [README.rst](README.rst) with detailed installation and usage instructions.*
