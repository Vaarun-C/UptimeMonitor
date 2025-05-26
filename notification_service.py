import smtplib
import os
from datetime import datetime
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database_manager import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

class NotificationService:    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("APP_PASSWORD")
        
        if not all([self.email_user, self.email_password]):
            print("⚠️ Email credentials not configured - notifications disabled")
            self.email_enabled = False
        else:
            self.email_enabled = True
            print("✅ Email notifications enabled")
    
    def send_user_uptime_summary(self, user_id: int, user_email: str):
        if not self.email_enabled:
            print("📧 Email not configured - skipping notification")
            return False
            
        try:
            user_urls = self.db_manager.get_user_urls(user_id)
            if not user_urls:
                print(f"📝 No URLs for user {user_id} - skipping email")
                return False
            
            summary_data = []
            down_sites = 0
            
            for url_data in user_urls:
                status = self.db_manager.get_url_status(url_data["url"], user_id)
                if status:
                    summary_data.append(status)

                    if status.get("uptime_percentage", 100) < 99:  # Consider <99% as having issues
                        down_sites += 1
            

            user_info = self.db_manager.get_user_info(user_id)  # You'll need to implement this
            username = user_info.get("username", "User") if user_info else "User"
            
            email_body = self.create_user_summary_email(
                username, summary_data, len(user_urls), down_sites
            )
            
            if down_sites > 0:
                subject = f"🚨 {username}: {down_sites} site(s) need attention - Uptime Report"
            else:
                subject = f"✅ {username}: All systems operational - Uptime Report"
            
            success = self.send_email(user_email, subject, email_body)
            
            if success:
                print(f"📧 Email summary sent to {username} ({user_email})")
                return True
            else:
                print(f"❌ Failed to send email to {username}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send notification to user {user_id}: {str(e)}")
            return False
    
    def send_notifications_to_all_users(self):
        if not self.email_enabled:
            print("📧 Email not configured - skipping all notifications")
            return
            
        try:
            users_with_urls = self.db_manager.get_users_with_urls()
            
            if not users_with_urls:
                print("📝 No users with URLs to notify")
                return
            
            print(f"📧 Sending notifications to {len(users_with_urls)} users...")
            
            for user_data in users_with_urls:
                user_id = user_data["user_id"]
                user_email = user_data.get("email")
                
                self.send_user_uptime_summary(user_id, user_email)
            
        except Exception as e:
            print(f"❌ Failed to send notifications to users: {str(e)}")
    
    def create_user_summary_email(self, username: str, summary_data: List[Dict], total_sites: int, down_sites: int) -> str:
        overall_status = "🟢 All your sites are operational" if down_sites == 0 else f"🔴 {down_sites} of your sites need attention"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .success {{ color: #28a745; font-weight: bold; }}
                .warning {{ color: #ffc107; font-weight: bold; }}
                .error {{ color: #dc3545; font-weight: bold; }}
                .footer {{ margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔍 Your Uptime Monitoring Report</h2>
                <p><strong>Hello {username}!</strong></p>
                <p><strong>Report generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="summary">
                <h3>Overall Status</h3>
                <p><strong>{overall_status}</strong></p>
                <ul>
                    <li>Your monitored sites: <strong>{total_sites}</strong></li>
                    <li>Sites operational: <strong>{total_sites - down_sites}</strong></li>
                    <li>Sites needing attention: <strong>{down_sites}</strong></li>
                </ul>
            </div>
            
            <h3>Your Site Status Details</h3>
            <table>
                <tr>
                    <th>URL</th>
                    <th>Uptime %</th>
                    <th>Category</th>
                    <th>Last Checked</th>
                </tr>
        """
        
        for site in summary_data:
            uptime = site.get("uptime_percentage", 0)
            
            if uptime >= 99:
                uptime_class = "success"
                uptime_color = "#28a745"
            elif uptime >= 95:
                uptime_class = "warning"
                uptime_color = "#ffc107"
            else:
                uptime_class = "error"
                uptime_color = "#dc3545"
            
            category = site.get("category", "Uncategorized")
            last_checked = site.get("last_checked", "Never")
            
            html_content += f"""
                <tr>
                    <td><a href="{site['url']}" target="_blank">{site['url']}</a></td>
                    <td class="{uptime_class}" style="color: {uptime_color};">{uptime}%</td>
                    <td>{category}</td>
                    <td>{last_checked}</td>
                </tr>
            """
        
        html_content += f"""
            </table>
            
            <div class="footer">
                <p><strong>Uptime Monitoring Service</strong></p>
                <p>This is your personalized uptime report for {username}.</p>
                <p>You can manage your monitored URLs and view detailed logs through the API dashboard.</p>
                <p><em>Uptime percentages are calculated based on checks from the last 24 hours.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        try:
            print(f"🔧 Sending email to {recipient_email}")
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_user
            message["To"] = recipient_email
            
            html_part = MIMEText(body, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                server.login(self.email_user, self.email_password)
                server.send_message(message)
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print("❌ SMTP Authentication failed. Check your email credentials.")
            print("💡 For Gmail, you need:")
            print("   1. Enable 2-Factor Authentication")
            print("   2. Generate an App Password (not your regular password)")
            print("   3. Use the 16-character App Password")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            print(f"❌ Recipient email address refused: {recipient_email}")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False