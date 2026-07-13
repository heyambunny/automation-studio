# services/email_composer.py
from datetime import datetime
from typing import Dict
import re

class EmailComposer:
    """Composes emails by resolving template variables"""
    
    @staticmethod
    def resolve_template(template: str, variables: Dict[str, str]) -> str:
        """
        Replace {{variable}} placeholders with values.
        """
        resolved = template
        
        variables["CurrentDate"] = datetime.now().strftime("%Y-%m-%d")
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            resolved = resolved.replace(placeholder, str(value) if value else "")
        
        return resolved
    
    @staticmethod
    def compose_email(
        subject_template: str,
        body_template: str,
        summary_html: str,
        branch_name: str,
        variables: Dict[str, str],
        sender_name: str = "",
        signature: str = ""
    ) -> Dict[str, str]:
        branch_vars = variables.copy()
        branch_vars["BranchName"] = branch_name
        branch_vars["Summary"] = summary_html or ""
        branch_vars["SenderName"] = sender_name or "Automation Studio"
        branch_vars["Signature"] = signature or ""
        
        subject = EmailComposer.resolve_template(subject_template, branch_vars)
        body = EmailComposer.resolve_template(body_template, branch_vars)
        
        if not body.strip():
            body = summary_html
        
        # Keep intentional blank lines, remove excessive ones
        body = re.sub(r'\n{3,}', '\n\n', body)
        
        # Convert \n\n to <br><br>
        body = body.replace('\n\n', '<br><br>')
        
        # Convert remaining \n to <br>
        body = body.replace('\n', '<br>')
        
        # Clean excess whitespace around HTML table
        body = re.sub(r'<br>\s*<table', '<br><table', body)
        body = re.sub(r'</table>\s*<br>', '</table><br>', body)
        
        # Remove leading/trailing <br> around tables
        body = re.sub(r'<br><br>(<table)', r'<br>\1', body)
        body = re.sub(r'(</table>)<br><br>', r'\1<br>', body)
        
        # Remove 3+ <br> tags, keep max 2
        body = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', body)
        
        # Wrap in HTML
        if body and "<html>" not in body.lower():
            body = f"""<html>
<body style="font-family: Arial, sans-serif;">
<div style="padding: 20px;">
{body}
</div>
</body>
</html>"""
        
        return {
            "subject": subject.strip(),
            "html_body": body
        }