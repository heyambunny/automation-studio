# services/email_composer.py
from datetime import datetime
from typing import Dict
import re

class EmailComposer:
    """Composes emails by resolving template variables"""
    
    @staticmethod
    def resolve_template(template: str, variables: Dict[str, str], cell_data: Dict[str, str] = None) -> str:
        resolved = template
        
        variables["CurrentDate"] = datetime.now().strftime("%Y-%m-%d")
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            resolved = resolved.replace(placeholder, str(value) if value else "")
        
        if cell_data:
            def replace_cell(match):
                ref = match.group(1)
                if '!' in ref:
                    key = ref
                else:
                    key = f"Sheet1!{ref}"
                val = cell_data.get(key, cell_data.get(ref, ""))
                return str(val) if val else match.group(0)
            
            resolved = re.sub(r'\{\{Cell:(.*?)\}\}', replace_cell, resolved)
        
        return resolved
    
    @staticmethod
    def compose_email(
        subject_template: str,
        body_template: str,
        summary_html: str,
        branch_name: str,
        variables: Dict[str, str],
        cell_data: Dict[str, str] = None,
        sender_name: str = "",
        signature: str = ""
    ) -> Dict[str, str]:
        branch_vars = variables.copy()
        branch_vars["BranchName"] = branch_name
        branch_vars["Summary"] = summary_html or ""
        branch_vars["SenderName"] = sender_name or "Automation Studio"
        branch_vars["Signature"] = signature or ""
        
        subject = EmailComposer.resolve_template(subject_template, branch_vars, cell_data)
        body = EmailComposer.resolve_template(body_template, branch_vars, cell_data)
        
        if not body.strip():
            body = summary_html
        
        body = re.sub(r'\n{2,}', '\n\n', body)
        body = body.replace('\n\n', '<br><br>')
        body = body.replace('\n', '<br>')
        body = re.sub(r'<br>\s*<table', '<br><table', body)
        body = re.sub(r'</table>\s*<br>', '</table><br>', body)
        body = re.sub(r'<br><br>(<table)', r'<br>\1', body)
        body = re.sub(r'(</table>)<br><br>', r'\1<br>', body)
        body = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', body)
        
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