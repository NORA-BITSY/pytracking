# PyTracking Server Deployment Checklist

## 🖥️ Server Setup (143.110.214.80)

### Prerequisites
- [ ] Server is running Ubuntu 20.04+ or Debian 10+
- [ ] You have root SSH access to the server
- [ ] Domain `realproductpat.com` is pointed to IP `143.110.214.80`

### Step 1: Deploy Infrastructure
```bash
# SSH to your server
ssh root@143.110.214.80

# Upload deployment script
scp deploy_server.sh root@143.110.214.80:/root/

# Make it executable and run
chmod +x /root/deploy_server.sh
./deploy_server.sh
```

### Step 2: Upload Application Files
From your local machine:
```bash
./upload_to_server.sh
```

### Step 3: Configure DNS
- [ ] Set A record: `realproductpat.com` → `143.110.214.80`
- [ ] Set A record: `www.realproductpat.com` → `143.110.214.80`
- [ ] Wait for DNS propagation (15-60 minutes)

### Step 4: SSL Certificate
On server:
```bash
# After DNS is propagated
sudo certbot --nginx -d realproductpat.com -d www.realproductpat.com
```

## 🔍 Testing Your Deployment

### 1. Health Check
Visit: `https://realproductpat.com/health`
Expected: `{"status": "healthy", "timestamp": "..."}`

### 2. Database Test
```bash
ssh root@143.110.214.80
su - pytracking
cd pytracking
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    database='pytracking',
    user='pytracking',
    password='secure_password_123'
)
print('Database connection: OK')
"
```

### 3. Tracking Test
Visit: `https://realproductpat.com/admin/events`
Should show empty tracking events list

### 4. Send Legal Email Test
```bash
# On server as pytracking user
cd pytracking
python3 generate_legal_email.py
```

## 📧 Email Integration

### Using SendGrid (Recommended)
1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Get API key
3. Install: `pip install sendgrid`
4. Add to your Flask app:

```python
import sendgrid
from sendgrid.helpers.mail import Mail

def send_tracked_email(to_email, subject, html_content):
    sg = sendgrid.SendGridAPIClient(api_key='YOUR_API_KEY')
    message = Mail(
        from_email='legal@realproductpat.com',
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    sg.send(message)
```

### Using SMTP
Add to your Flask app:
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_smtp(to_email, subject, html_content):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'legal@realproductpat.com'
    msg['To'] = to_email
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your_email@gmail.com', 'app_password')
        server.send_message(msg)
```

## 🔐 Security Checklist

- [ ] Firewall configured (ports 22, 80, 443 only)
- [ ] PostgreSQL not accessible externally
- [ ] SSL certificates auto-renewing
- [ ] Application running as non-root user
- [ ] Logs being rotated

## 📊 Monitoring

### View Logs
```bash
# Application logs
sudo tail -f /var/log/supervisor/pytracking.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### View Tracking Data
Visit: `https://realproductpat.com/admin/events`

## 🔄 Maintenance

### Restart Application
```bash
sudo supervisorctl restart pytracking
```

### Update Application
```bash
# Upload new files
./upload_to_server.sh

# Restart
ssh root@143.110.214.80 "sudo supervisorctl restart pytracking"
```

### Backup Database
```bash
ssh root@143.110.214.80
sudo -u postgres pg_dump pytracking > backup_$(date +%Y%m%d).sql
```

## 🚨 Troubleshooting

### Application Won't Start
```bash
sudo supervisorctl status pytracking
sudo tail -f /var/log/supervisor/pytracking.log
```

### SSL Issues
```bash
sudo nginx -t
sudo systemctl reload nginx
sudo certbot certificates
```

### Database Issues
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"
```

## 📋 Your Legal Email Tracking Setup

Your legal correspondence for **State v. White (Case 2025CF000089)** is ready with:

- ✅ Invisible tracking pixel
- ✅ Encrypted tracking data
- ✅ Open time logging
- ✅ IP address capture
- ✅ User agent tracking
- ✅ Webhook notifications

**Tracking URL Format:**
`https://realproductpat.com/track/open/{encrypted_data}`

**Generated Files:**
- `legal_correspondence_tracked.html` - Ready to send
- `legal_tracking_info.txt` - Tracking details for your records

---

## 🎯 Quick Start Summary

1. **Deploy**: `ssh root@143.110.214.80` → `./deploy_server.sh`
2. **Upload**: `./upload_to_server.sh` (from local machine)
3. **DNS**: Point `realproductpat.com` to `143.110.214.80`
4. **SSL**: `sudo certbot --nginx -d realproductpat.com`
5. **Test**: Visit `https://realproductpat.com/health`
6. **Send**: Use your generated tracked legal email

Your PyTracking system will be live at `https://realproductpat.com`! 🚀
