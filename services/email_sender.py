# services/email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
import os

class EmailSender:
    """Sends emails via SMTP"""
    
    def __init__(self, smtp_config: Dict[str, str]):
        """
        smtp_config: {
            server, port, email, password, use_tls, sender_name
        }
        """
        self.server = smtp_config.get("server", "")
        self.port = int(smtp_config.get("port", 587))
        self.email = smtp_config.get("email", "")
        self.password = smtp_config.get("password", "")
        self.use_tls = smtp_config.get("use_tls", True)
        self.sender_name = smtp_config.get("sender_name", "")
    
    def test_connection(self) -> Dict[str, any]:
        """Test SMTP connection and authentication"""
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.server, self.port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.server, self.port, timeout=10)
            
            server.login(self.email, self.password)
            server.quit()
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        html_body: str,
        cc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Send an email with optional CC and attachments.
        Returns {success: bool, message: str}
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.sender_name} <{self.email}>" if self.sender_name else self.email
            msg["To"] = ", ".join(to_recipients)
            msg["Subject"] = subject
            
            if cc_recipients:
                msg["Cc"] = ", ".join(cc_recipients)
                all_recipients = to_recipients + cc_recipients
            else:
                all_recipients = to_recipients
            
            # Attach HTML body
            msg.attach(MIMEText(html_body, "html"))
            
            # Attach files
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={os.path.basename(file_path)}"
                            )
                            msg.attach(part)
            
            # Send
            if self.use_tls:
                server = smtplib.SMTP(self.server, self.port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.server, self.port, timeout=30)
            
            server.login(self.email, self.password)
            server.sendmail(self.email, all_recipients, msg.as_string())
            server.quit()
            
            return {"success": True, "message": "Email sent successfully"}
        
        except Exception as e:
            return {"success": False, "message": str(e)}