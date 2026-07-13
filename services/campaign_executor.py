# services/campaign_executor.py
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from services.file_scanner import FileScanner
from services.excel_reader import ExcelReader
from services.email_composer import EmailComposer
from services.email_sender import EmailSender
from services.ai_service import AIService
from models import Execution, EmailLog, SMTPProfile, MappingEntry, Setting


class CampaignExecutor:
    """Executes a complete email campaign"""
    
    def __init__(self, execution_id: int, config: Dict, db: Session):
        self.execution_id = execution_id
        self.config = config
        self.db = db
        
        self.execution = db.query(Execution).filter_by(id=execution_id).first()
        
        setting = db.query(Setting).first()
        self.folder_path = config.get("campaign_folder") or (setting.folder_path if setting else "")
        self.sheet_name = config.get("sheet_name", "Summary")
        self.start_cell = config.get("start_cell", "B5")
        
        self.smtp_sender = None
        if "SMTP" in config.get("send_method", ""):
            profile_name = config.get("smtp_profile", "")
            profile = db.query(SMTPProfile).filter_by(profile_name=profile_name).first()
            if profile:
                self.smtp_sender = EmailSender({
                    "server": profile.smtp_server,
                    "port": profile.smtp_port,
                    "email": profile.sender_email,
                    "password": profile.password,
                    "use_tls": profile.use_tls,
                    "sender_name": profile.sender_name or ""
                })
        
        self.ai_service = AIService()
    
    def _format_ai_for_email(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'^Subject:\s*', '', text.strip())
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        lines = text.split('\n')
        formatted = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('- ') or stripped.startswith('• '):
                if not in_list:
                    formatted.append('<ul style="margin:0;padding-left:18px;">')
                    in_list = True
                formatted.append(f'<li style="margin:0;font-size:14px;">{stripped[2:]}</li>')
            else:
                if in_list:
                    formatted.append('</ul>')
                    in_list = False
                formatted.append(f'<p style="margin:0;font-size:14px;">{stripped}</p>')
        
        if in_list:
            formatted.append('</ul>')
        return ''.join(formatted)
    
    def execute(self) -> Dict:
        try:
            self.execution.status = "in_progress"
            self.execution.started_at = datetime.utcnow()
            self.db.commit()
            
            entries = self._get_branch_entries()
            
            scanner = FileScanner(self.folder_path)
            branch_names = [e["branch_name"] for e in entries]
            file_matches = scanner.match_branches(branch_names)
            
            mode = self.config.get("mode", "static/static")
            ai_option = self.config.get("ai_option", "auto")
            variables = self.config.get("variables", {})
            report_type = variables.get("ReportType", "") or "Performance Report"
            sender_name = self.smtp_sender.sender_name if self.smtp_sender else "Automation Studio"
            user_context = self.config.get("user_context", "")
            attach_file = self.config.get("attach_file", True)
            group_var = self.config.get("group_var", "BranchName")
            group_var_placeholder = self.config.get("group_var_placeholder", "{{BranchName}}")
            
            # Generate subject ONCE for all branches
            if mode == "ai/ai" and ai_option != "prompt_only":
                all_text = ""
                for entry in entries:
                    file_path = file_matches.get(entry["branch_name"])
                    if file_path:
                        summary_df = ExcelReader.detect_active_range(file_path, self.sheet_name, self.start_cell)
                        st = ExcelReader.dataframe_to_text(summary_df) if summary_df is not None else ""
                        if st:
                            all_text += st[:500] + "\n"
                
                if all_text:
                    ai_subject = self.ai_service.generate_subject(all_text, user_context)
                else:
                    ai_subject = None
                campaign_subject = ai_subject if ai_subject else f"{report_type} - Performance Summary"
            elif mode == "ai/ai" and ai_option == "prompt_only":
                ai_subject = self.ai_service.generate_subject(user_context, user_context) if user_context else None
                campaign_subject = ai_subject if ai_subject else report_type
            else:
                campaign_subject = self.config.get("subject", "") or f"{report_type} - {group_var_placeholder}"
            
            # For prompt_only, generate ONE body
            prompt_only_body = ""
            if mode == "ai/ai" and ai_option == "prompt_only":
                prompt_only_body = self.ai_service.generate_from_prompt_only(user_context) or ""
                prompt_only_body = self._format_ai_for_email(prompt_only_body)
            
            # Process each branch
            results = []
            
            for entry in entries:
                branch = entry["branch_name"]
                to_list = [e.strip() for e in entry["to"].replace(";", ",").split(",") if e.strip()]
                cc_list = [e.strip() for e in entry["cc"].replace(";", ",").split(",") if e.strip()] if entry.get("cc") else []
                
                file_path = file_matches.get(branch)
                attachment_path = file_path if attach_file else None
                
                if not file_path and attach_file and ai_option != "prompt_only":
                    self._log_email(branch, to_list, cc_list, "", "failed", "File not found")
                    results.append({"branch": branch, "status": "failed", "reason": "File not found"})
                    continue
                
                summary_df = None
                summary_text = ""
                summary_html = ""
                
                if file_path:
                    summary_df = ExcelReader.detect_active_range(file_path, self.sheet_name, self.start_cell)
                    summary_text = ExcelReader.dataframe_to_text(summary_df) if summary_df is not None else ""
                    summary_html = ExcelReader.dataframe_to_html(summary_df) if summary_df is not None else ""
                
                ai_summary = ""
                if mode == "ai/ai":
                    if ai_option == "prompt_only":
                        ai_summary = prompt_only_body
                    elif ai_option == "guided" and summary_text:
                        ai_summary = self.ai_service.generate_summary(summary_text, user_context) or ""
                        ai_summary = self._format_ai_for_email(ai_summary)
                    elif summary_text:
                        ai_summary = self.ai_service.generate_summary(summary_text) or ""
                        ai_summary = self._format_ai_for_email(ai_summary)
                
                # Build email body
                if mode == "static/static":
                    user_body_template = self.config.get("body_template", "")
                    if user_body_template:
                        body_vars = variables.copy()
                        body_vars[group_var] = branch
                        body_vars["Summary"] = summary_html
                        body_vars["SenderName"] = sender_name
                        body_vars["ReportType"] = report_type
                        body_vars["CurrentDate"] = datetime.utcnow().strftime("%Y-%m-%d")
                        
                        email_body = user_body_template
                        email_body = email_body.replace(group_var_placeholder, branch)
                        for key, value in body_vars.items():
                            email_body = email_body.replace(f"{{{{{key}}}}}", str(value) if value else "")
                        email_body = email_body.replace("\n", "<br>")
                    else:
                        email_body = f"""<p style="margin:0 0 3px 0;">Dear <strong>{branch}</strong> Team,</p>
<p style="margin:0 0 3px 0;">Please find attached the <strong>{report_type}</strong> for your branch.</p>
<p style="margin:6px 0 0 0;">Thanks &amp; Regards,<br><strong>{sender_name}</strong></p>"""
                else:
                    email_body = f"""<p style="margin:0 0 3px 0;">Dear <strong>{branch}</strong> Team,</p>"""
                    
                    if ai_summary:
                        email_body += f"""<div style="background-color:#f5f5f5;padding:8px 12px;border-radius:5px;margin:6px 0;">
<h4 style="margin:0 0 3px 0;color:#333;font-size:15px;">📊 Summary</h4>
{ai_summary}
</div>"""
                    else:
                        email_body += f"""<p style="margin:0 0 3px 0;">Please find the {report_type} details below.</p>"""
                    
                    if attach_file and file_path:
                        email_body += f"""<p style="margin:0 0 3px 0;">📎 The detailed report is attached.</p>"""
                    
                    email_body += f"""<p style="margin:6px 0 0 0;">Thanks &amp; Regards,<br><strong>{sender_name}</strong></p>"""
                
                # Subject line
                branch_subject = campaign_subject.replace(group_var_placeholder, branch)
                branch_subject = re.sub(r'^Subject:\s*', '', branch_subject.strip())
                
                # Compose email
                email = EmailComposer.compose_email(
                    subject_template=branch_subject,
                    body_template=email_body,
                    summary_html="",
                    branch_name=branch,
                    variables=variables,
                    sender_name=sender_name,
                    signature=""
                )
                
                # Send
                if "Outlook" in self.config.get("send_method", ""):
                    from services.outlook_service import OutlookService
                    outlook = OutlookService()
                    
                    if outlook.is_available():
                        if "Drafts" in self.config.get("send_method", ""):
                            result = outlook.save_draft(to_list, email["subject"], email["html_body"], cc_list, [file_path] if file_path else [])
                            status = "draft_saved" if result["success"] else "failed"
                        else:
                            result = outlook.send_email(to_list, email["subject"], email["html_body"], cc_list, [file_path] if file_path else [])
                            status = "sent" if result["success"] else "failed"
                        error = result.get("message", "") if not result["success"] else ""
                    else:
                        status = "failed"
                        error = "Outlook not available"
                elif self.smtp_sender:
                    attachments = [attachment_path] if attachment_path and os.path.exists(attachment_path) else []
                    result = self.smtp_sender.send_email(
                        to_recipients=to_list,
                        subject=email["subject"],
                        html_body=email["html_body"],
                        cc_recipients=cc_list,
                        attachments=attachments
                    )
                    status = "sent" if result["success"] else "failed"
                    error = result.get("message", "") if not result["success"] else ""
                else:
                    status = "failed"
                    error = "No valid send method configured"
                
                self._log_email(branch, to_list, cc_list, email["subject"], status, error)
                results.append({"branch": branch, "status": status, "error": error})
            
            self.execution.status = "completed"
            self.execution.completed_at = datetime.utcnow()
            self.execution.total_emails = len(results)
            self.execution.sent_count = sum(1 for r in results if r["status"] == "sent")
            self.execution.failed_count = sum(1 for r in results if r["status"] == "failed")
            self.db.commit()
            
            return {"success": True, "results": results}
        
        except Exception as e:
            self.execution.status = "failed"
            self.execution.error_message = str(e)
            self.execution.completed_at = datetime.utcnow()
            self.db.commit()
            return {"success": False, "error": str(e)}
    
    def _get_branch_entries(self) -> List[Dict]:
        preview = self.config.get("preview_data", [])
        group_var = self.config.get("group_var", "BranchName")
        if preview:
            return [{"branch_name": p[group_var], "to": p["To"], "cc": p.get("CC", "")} for p in preview]
        
        mapping_id = self.config.get("mapping_id")
        if mapping_id:
            entries = self.db.query(MappingEntry).filter_by(mapping_id=mapping_id).all()
            return [{"branch_name": e.branch_name, "to": e.to_recipients, "cc": e.cc_recipients} for e in entries]
        elif self.config.get("temp_mapping"):
            result = []
            for e in self.config["temp_mapping"]:
                keys = [k for k in e.keys() if k.lower() not in ["to", "cc"]]
                name_key = keys[0] if keys else "BranchName"
                result.append({"branch_name": e[name_key], "to": e.get("To", ""), "cc": e.get("CC", "")})
            return result
        return []
    
    def _log_email(self, branch: str, to_list: List[str], cc_list: List[str], subject: str, status: str, error: str):
        log = EmailLog(
            execution_id=self.execution_id,
            branch_name=branch,
            recipient_to=", ".join(to_list),
            recipient_cc=", ".join(cc_list),
            subject=subject,
            status=status,
            error_message=error,
            sent_at=datetime.utcnow() if status in ["sent", "draft_saved"] else None
        )
        self.db.add(log)
        self.db.commit()