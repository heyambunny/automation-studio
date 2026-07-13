# services/scheduler_service.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from database import SessionLocal
from models import Schedule, Execution
from services.campaign_executor import CampaignExecutor
import json

class SchedulerService:
    """Manages scheduled campaigns"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._load_schedules()
    
    def _load_schedules(self):
        """Load all enabled schedules from database"""
        db = SessionLocal()
        schedules = db.query(Schedule).filter(Schedule.enabled == True).all()
        for s in schedules:
            self._add_job(s)
        db.close()
    
    def add_schedule(self, schedule_id: int, campaign_config: dict, frequency: str, 
                     schedule_date: str = None, schedule_time: str = None, cron: str = None):
        """Add a new scheduled campaign"""
        db = SessionLocal()
        
        schedule = Schedule(
            user_id=1,
            schedule_name=campaign_config.get("variables", {}).get("ReportType", "Scheduled Campaign"),
            campaign_config=json.dumps(campaign_config),
            frequency=frequency,
            cron_expression=cron,
            enabled=True
        )
        
        # Set next run time
        if frequency == "once" and schedule_date and schedule_time:
            run_time = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M:%S")
            schedule.next_run = run_time
        elif frequency == "daily":
            schedule.next_run = self._next_daily(schedule_time or "09:00")
        elif frequency == "weekly":
            schedule.next_run = self._next_weekly(schedule_time or "09:00")
        elif frequency == "monthly":
            schedule.next_run = self._next_monthly(schedule_time or "09:00")
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        self._add_job(schedule)
        db.close()
        
        return schedule.id
    
    def _add_job(self, schedule):
        """Add a job to APScheduler"""
        config = json.loads(schedule.campaign_config) if schedule.campaign_config else {}
        
        if schedule.frequency == "once":
            trigger = DateTrigger(run_date=schedule.next_run)
        elif schedule.frequency == "custom" and schedule.cron_expression:
            trigger = CronTrigger.from_crontab(schedule.cron_expression)
        elif schedule.frequency == "daily":
            hour, minute = self._parse_time(schedule.next_run)
            trigger = CronTrigger(hour=hour, minute=minute)
        elif schedule.frequency == "weekly":
            hour, minute = self._parse_time(schedule.next_run)
            trigger = CronTrigger(day_of_week='mon', hour=hour, minute=minute)
        elif schedule.frequency == "monthly":
            hour, minute = self._parse_time(schedule.next_run)
            trigger = CronTrigger(day=1, hour=hour, minute=minute)
        else:
            return
        
        self.scheduler.add_job(
            func=self._execute_scheduled_campaign,
            trigger=trigger,
            args=[schedule.id, config],
            id=f"schedule_{schedule.id}",
            replace_existing=True
        )
    
    def _execute_scheduled_campaign(self, schedule_id: int, config: dict):
        """Execute a scheduled campaign"""
        db = SessionLocal()
        
        try:
            # Create execution record
            execution = Execution(
                user_id=1,
                campaign_name=f"Scheduled: {config.get('variables', {}).get('ReportType', 'Campaign')}",
                status="queued",
                send_method=config.get("send_method", "SMTP"),
                mode=config.get("mode", "static/static"),
                total_emails=0
            )
            db.add(execution)
            db.commit()
            
            # Execute
            executor = CampaignExecutor(execution.id, config, db)
            result = executor.execute()
            
            # Update schedule next run
            schedule = db.query(Schedule).filter_by(id=schedule_id).first()
            if schedule and schedule.frequency != "once":
                if schedule.frequency == "daily":
                    schedule.next_run = self._next_daily()
                elif schedule.frequency == "weekly":
                    schedule.next_run = self._next_weekly()
                elif schedule.frequency == "monthly":
                    schedule.next_run = self._next_monthly()
                db.commit()
            elif schedule and schedule.frequency == "once":
                schedule.enabled = False
                db.commit()
            
        except Exception as e:
            execution = db.query(Execution).filter_by(id=execution.id).first() if 'execution' in locals() else None
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                db.commit()
        finally:
            db.close()
    
    def remove_schedule(self, schedule_id: int):
        """Remove a schedule"""
        try:
            self.scheduler.remove_job(f"schedule_{schedule_id}")
        except:
            pass
        
        db = SessionLocal()
        schedule = db.query(Schedule).filter_by(id=schedule_id).first()
        if schedule:
            schedule.enabled = False
            db.commit()
        db.close()
    
    def _parse_time(self, run_time):
        """Parse time from datetime or string"""
        if isinstance(run_time, datetime):
            return run_time.hour, run_time.minute
        if isinstance(run_time, str):
            parts = run_time.split(":")
            return int(parts[0]), int(parts[1])
        return 9, 0
    
    def _next_daily(self, time_str: str = "09:00"):
        """Get next daily run time"""
        hour, minute = self._parse_time(time_str)
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            from datetime import timedelta
            next_run += timedelta(days=1)
        return next_run
    
    def _next_weekly(self, time_str: str = "09:00"):
        """Get next weekly run time (Monday)"""
        hour, minute = self._parse_time(time_str)
        now = datetime.now()
        from datetime import timedelta
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_until_monday)
        return next_run
    
    def _next_monthly(self, time_str: str = "09:00"):
        """Get next monthly run time (1st of month)"""
        hour, minute = self._parse_time(time_str)
        now = datetime.now()
        from datetime import timedelta
        import calendar
        if now.month == 12:
            next_month = now.replace(year=now.year+1, month=1, day=1, hour=hour, minute=minute, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month+1, day=1, hour=hour, minute=minute, second=0, microsecond=0)
        return next_month
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
            })
        return jobs


# Global scheduler instance
scheduler_service = SchedulerService()