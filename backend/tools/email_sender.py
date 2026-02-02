import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from pathlib import Path
from typing import List, Optional

class EmailSender:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")
        
        if not self.user or not self.password:
            # Try loading from ~/.smtp_config or similar if env not set, 
            # but for now we'll stick to env vars as primary for security.
            pass

    def send_email(self, 
                   to_email: str, 
                   subject: str, 
                   body: str, 
                   html: bool = False, 
                   attachments: Optional[List[str]] = None) -> str:
        
        if not self.user or not self.password:
            return "Error: SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD environment variables."

        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach body
        msg.attach(MIMEText(body, 'html' if html else 'plain'))

        # Attach files
        if attachments:
            for fpath in attachments:
                path = Path(fpath)
                if path.exists():
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                    part['Content-Disposition'] = f'attachment; filename="{path.name}"'
                    msg.attach(part)
                else:
                    return f"Error: Attachment not found: {fpath}"

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            return f"Email successfully sent to {to_email}"
        except Exception as e:
            return f"Failed to send email: {str(e)}"

def send_email_tool(to: str, subject: str, body: str, html: bool = False, attachments: str = None) -> str:
    """Send an email via SMTP."""
    sender = EmailSender()
    attach_list = attachments.split(",") if attachments else None
    return sender.send_email(to, subject, body, html, attach_list)
