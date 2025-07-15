#!/usr/bin/env python3
"""
Advanced Honeypot Management System for PyTracking Server
Real-time threat intelligence and automated response
"""

import os
import sys
import json
import time
import sqlite3
import logging
import subprocess
import threading
from datetime import datetime, timedelta
import ipaddress
import requests
from collections import defaultdict

class ThreatIntelligence:
    """Advanced threat detection and response system"""
    
    def __init__(self):
        self.db_path = "/var/lib/security/threats.db"
        self.log_file = "/var/log/security/threat_intel.log"
        self.blocked_ips = set()
        self.threat_patterns = {
            'ssh_bruteforce': r'Failed password.*from (\d+\.\d+\.\d+\.\d+)',
            'web_exploit': r'(union.*select|script.*alert|eval\(|base64_decode)',
            'directory_traversal': r'\.\./|\.\.\\\|etc/passwd|etc/shadow',
            'sql_injection': r"('.*or.*'|union.*select|drop.*table)",
            'xss_attempt': r'(<script|javascript:|onload=|onerror=)',
            'command_injection': r'(;.*ls|;.*cat|;.*wget|;.*curl|\|.*nc)',
        }
        self.setup_database()
        self.setup_logging()
    
    def setup_database(self):
        """Initialize threat intelligence database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                severity INTEGER DEFAULT 1,
                details TEXT,
                geo_location TEXT,
                user_agent TEXT,
                blocked BOOLEAN DEFAULT FALSE,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                attempt_count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_reputation (
                ip_address TEXT PRIMARY KEY,
                reputation_score INTEGER DEFAULT 0,
                is_malicious BOOLEAN DEFAULT FALSE,
                country TEXT,
                asn TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_threats_ip ON threats(ip_address);
            CREATE INDEX IF NOT EXISTS idx_threats_timestamp ON threats(timestamp);
            CREATE INDEX IF NOT EXISTS idx_threats_type ON threats(threat_type);
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_logging(self):
        """Setup advanced logging"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_ip_geolocation(self, ip):
        """Get geolocation data for IP address"""
        try:
            # Using ipapi.co for geolocation (free tier)
            response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'country': data.get('country_name', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'asn': data.get('asn', 'Unknown'),
                    'org': data.get('org', 'Unknown')
                }
        except Exception as e:
            self.logger.warning(f"Failed to get geolocation for {ip}: {e}")
        
        return {'country': 'Unknown', 'city': 'Unknown', 'asn': 'Unknown', 'org': 'Unknown'}
    
    def check_ip_reputation(self, ip):
        """Check IP reputation against threat intelligence feeds"""
        reputation_score = 0
        is_malicious = False
        
        try:
            # Check if IP is in known malicious ranges
            malicious_ranges = [
                '10.0.0.0/8',      # Private ranges shouldn't access from internet
                '172.16.0.0/12',
                '192.168.0.0/16',
            ]
            
            ip_obj = ipaddress.ip_address(ip)
            
            # Skip reputation check for your allowed IP
            if ip == "96.2.2.124":  # Your IP
                return 100, False  # High reputation, not malicious
            
            # Check against known bad ranges
            for bad_range in malicious_ranges:
                if ip_obj in ipaddress.ip_network(bad_range):
                    reputation_score -= 50
                    is_malicious = True
            
            # Additional checks could include:
            # - AbuseIPDB API
            # - VirusTotal API  
            # - Custom threat feeds
            
        except Exception as e:
            self.logger.error(f"Error checking IP reputation for {ip}: {e}")
        
        return reputation_score, is_malicious
    
    def record_threat(self, ip, threat_type, details, severity=1, user_agent=None):
        """Record threat in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if IP already exists
        cursor.execute(
            'SELECT id, attempt_count FROM threats WHERE ip_address = ? AND threat_type = ?',
            (ip, threat_type)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE threats 
                SET last_seen = CURRENT_TIMESTAMP, 
                    attempt_count = attempt_count + 1,
                    details = ?
                WHERE id = ?
            ''', (details, existing[0]))
            attempt_count = existing[1] + 1
        else:
            # Get geolocation data
            geo_data = self.get_ip_geolocation(ip)
            geo_location = f"{geo_data['city']}, {geo_data['country']} ({geo_data['asn']})"
            
            # Insert new record
            cursor.execute('''
                INSERT INTO threats 
                (ip_address, threat_type, details, severity, geo_location, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ip, threat_type, details, severity, geo_location, user_agent))
            attempt_count = 1
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Threat recorded: {ip} - {threat_type} (Attempt #{attempt_count})")
        
        # Auto-block after multiple attempts
        if attempt_count >= 3:
            self.block_ip(ip, f"Multiple {threat_type} attempts")
    
    def block_ip(self, ip, reason):
        """Block IP address using iptables"""
        if ip in self.blocked_ips or ip == "96.2.2.124":  # Don't block your IP
            return
        
        try:
            # Add to iptables
            subprocess.run([
                'iptables', '-I', 'INPUT', '1', '-s', ip, '-j', 'DROP'
            ], check=True)
            
            # Add to UFW as backup
            subprocess.run([
                'ufw', 'insert', '1', 'deny', 'from', ip
            ], check=True)
            
            self.blocked_ips.add(ip)
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE threats SET blocked = TRUE WHERE ip_address = ?',
                (ip,)
            )
            conn.commit()
            conn.close()
            
            self.logger.warning(f"BLOCKED IP: {ip} - Reason: {reason}")
            
            # Log to honeypot log for fail2ban integration
            with open('/var/log/security/honeypot.log', 'a') as f:
                f.write(f"{datetime.now()} AUTO_BLOCK IP:{ip} REASON:{reason}\n")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to block IP {ip}: {e}")
    
    def analyze_web_logs(self):
        """Analyze nginx access logs for threats"""
        access_log = "/var/log/nginx/access.log"
        
        if not os.path.exists(access_log):
            return
        
        try:
            # Read recent log entries
            with open(access_log, 'r') as f:
                lines = f.readlines()[-1000:]  # Last 1000 requests
            
            for line in lines:
                parts = line.split()
                if len(parts) < 10:
                    continue
                
                ip = parts[0]
                timestamp = parts[3] + " " + parts[4]
                method = parts[5].strip('"')
                url = parts[6]
                user_agent = " ".join(parts[11:]).strip('"')
                
                # Skip your IP
                if ip == "96.2.2.124":
                    continue
                
                # Check for threat patterns
                full_request = f"{method} {url} {user_agent}".lower()
                
                for threat_type, pattern in self.threat_patterns.items():
                    if any(p in full_request for p in pattern.split('|')):
                        self.record_threat(
                            ip, 
                            f"web_{threat_type}", 
                            f"Suspicious request: {method} {url}",
                            severity=3,
                            user_agent=user_agent
                        )
                        break
                
                # Check for automated tools
                suspicious_agents = [
                    'nmap', 'nikto', 'sqlmap', 'dirb', 'gobuster', 
                    'masscan', 'zap', 'burp', 'python-requests',
                    'curl', 'wget'
                ]
                
                if any(agent in user_agent.lower() for agent in suspicious_agents):
                    self.record_threat(
                        ip,
                        "web_scan",
                        f"Automated scanning tool detected: {user_agent}",
                        severity=2,
                        user_agent=user_agent
                    )
        
        except Exception as e:
            self.logger.error(f"Error analyzing web logs: {e}")
    
    def analyze_ssh_logs(self):
        """Analyze SSH logs for brute force attempts"""
        auth_log = "/var/log/auth.log"
        
        if not os.path.exists(auth_log):
            return
        
        try:
            # Read recent SSH failures
            result = subprocess.run([
                'grep', '-i', 'failed password', auth_log
            ], capture_output=True, text=True)
            
            recent_failures = result.stdout.split('\n')[-100:]  # Last 100 failures
            
            for line in recent_failures:
                if not line.strip():
                    continue
                
                # Extract IP from SSH log
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'from':
                        ip = parts[i + 1]
                        
                        # Skip your IP
                        if ip == "96.2.2.124":
                            continue
                        
                        # Extract username if available
                        username = "unknown"
                        if 'invalid user' in line.lower():
                            user_idx = line.lower().find('invalid user') + 12
                            username = line[user_idx:].split()[0]
                        
                        self.record_threat(
                            ip,
                            "ssh_bruteforce",
                            f"Failed SSH login attempt for user: {username}",
                            severity=3
                        )
                        break
        
        except Exception as e:
            self.logger.error(f"Error analyzing SSH logs: {e}")
    
    def generate_threat_report(self):
        """Generate comprehensive threat report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get threat statistics
        cursor.execute('''
            SELECT 
                threat_type,
                COUNT(*) as count,
                COUNT(DISTINCT ip_address) as unique_ips,
                MAX(last_seen) as latest_attempt
            FROM threats 
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY threat_type
            ORDER BY count DESC
        ''')
        
        threat_stats = cursor.fetchall()
        
        # Get top attacking IPs
        cursor.execute('''
            SELECT 
                ip_address,
                COUNT(*) as attempts,
                GROUP_CONCAT(DISTINCT threat_type) as attack_types,
                geo_location,
                blocked
            FROM threats 
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY ip_address
            ORDER BY attempts DESC
            LIMIT 10
        ''')
        
        top_attackers = cursor.fetchall()
        
        conn.close()
        
        # Generate report
        report = f"""
PYTRACKING SECURITY THREAT REPORT
================================
Generated: {datetime.now()}
Period: Last 24 hours

THREAT SUMMARY:
--------------
"""
        
        if threat_stats:
            for threat_type, count, unique_ips, latest in threat_stats:
                report += f"• {threat_type}: {count} attempts from {unique_ips} IPs (Latest: {latest})\n"
        else:
            report += "• No threats detected in the last 24 hours\n"
        
        report += f"""
TOP ATTACKING IPS:
-----------------
"""
        
        if top_attackers:
            for ip, attempts, attack_types, geo, blocked in top_attackers:
                status = "BLOCKED" if blocked else "MONITORING"
                report += f"• {ip}: {attempts} attempts ({attack_types}) - {geo} [{status}]\n"
        else:
            report += "• No significant attack sources identified\n"
        
        # Save report
        report_file = f"/var/log/security/threat_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.logger.info(f"Threat report generated: {report_file}")
        return report
    
    def run_continuous_monitoring(self):
        """Main monitoring loop"""
        self.logger.info("Advanced Threat Intelligence System started")
        
        while True:
            try:
                self.analyze_web_logs()
                self.analyze_ssh_logs()
                
                # Generate report every hour
                if datetime.now().minute == 0:
                    self.generate_threat_report()
                
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("Threat Intelligence System stopped")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    threat_intel = ThreatIntelligence()
    threat_intel.run_continuous_monitoring()
