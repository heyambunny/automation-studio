# services/outlook_service.py
import os
from typing import Dict, List, Optional

class OutlookService:
    """Send emails and save drafts via Outlook on Windows"""
    
    def __init__(self):
        self.outlook = None
        self._init_outlook()
    
    def _init_outlook(self):
        """Initialize Outlook connection"""
        try:
            import win32com.client
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            return True
        except:
            self.outlook = None
            return False
    
    def is_available(self) -> bool:
        return self.outlook is not None
    
    def send_email(self, to: List[str], subject: str, html_body: str, 
                   cc: List[str] = None, attachments: List[str] = None) -> Dict:
        """Send email via Outlook"""
        if not self.outlook:
            return {"success": False, "message": "Outlook not available on this system"}
        
        try:
            mail = self.outlook.CreateItem(0)  # 0 = olMailItem
            mail.To = "; ".join(to)
            mail.Subject = subject
            mail.HTMLBody = html_body
            
            if cc:
                mail.CC = "; ".join(cc)
            
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        mail.Attachments.Add(file_path)
            
            mail.Send()
            return {"success": True, "message": "Email sent via Outlook"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def save_draft(self, to: List[str], subject: str, html_body: str,
                   cc: List[str] = None, attachments: List[str] = None) -> Dict:
        """Save email as draft in Outlook"""
        if not self.outlook:
            return {"success": False, "message": "Outlook not available on this system"}
        
        try:
            mail = self.outlook.CreateItem(0)
            mail.To = "; ".join(to)
            mail.Subject = subject
            mail.HTMLBody = html_body
            
            if cc:
                mail.CC = "; ".join(cc)
            
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        mail.Attachments.Add(file_path)
            
            mail.Save()  # Saves to Drafts folder
            return {"success": True, "message": "Draft saved to Outlook"}
        except Exception as e:
            return {"success": False, "message": str(e)}