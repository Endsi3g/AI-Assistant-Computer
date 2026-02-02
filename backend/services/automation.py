"""
Automation Service
Task scheduling and automation using APScheduler
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
import re


class AutomationService:
    """Task automation and scheduling service"""
    
    def __init__(self):
        self.scheduler = None
        self.tasks = {}  # Store task metadata
        self._initialized = False
        print("[OK] Automation service ready")
    
    def _ensure_started(self):
        """Lazily start the scheduler when first needed"""
        if not self._initialized:
            try:
                from apscheduler.schedulers.asyncio import AsyncIOScheduler
                self.scheduler = AsyncIOScheduler()
                self.scheduler.start()
                self._initialized = True
            except Exception as e:
                print(f"[WARN] Could not start scheduler: {e}")
    
    
    def _parse_schedule(self, schedule_str: str) -> tuple:
        """Parse natural language schedule to APScheduler trigger"""
        schedule_lower = schedule_str.lower().strip()
        
        # "in X minutes/hours" pattern
        in_match = re.match(r'in\s+(\d+)\s+(minute|minutes|hour|hours|second|seconds)', schedule_lower)
        if in_match:
            amount = int(in_match.group(1))
            unit = in_match.group(2)
            
            if 'minute' in unit:
                delta = timedelta(minutes=amount)
            elif 'hour' in unit:
                delta = timedelta(hours=amount)
            else:
                delta = timedelta(seconds=amount)
            
            run_time = datetime.now() + delta
            return ('date', DateTrigger(run_date=run_time))
        
        # "every X minutes/hours" pattern
        every_match = re.match(r'every\s+(\d+)\s+(minute|minutes|hour|hours)', schedule_lower)
        if every_match:
            amount = int(every_match.group(1))
            unit = every_match.group(2)
            
            if 'minute' in unit:
                return ('interval', IntervalTrigger(minutes=amount))
            else:
                return ('interval', IntervalTrigger(hours=amount))
        
        # "every day at HH:MM" pattern
        daily_match = re.match(r'every\s+day\s+at\s+(\d{1,2}):?(\d{2})?(?:\s*(am|pm))?', schedule_lower)
        if daily_match:
            hour = int(daily_match.group(1))
            minute = int(daily_match.group(2) or 0)
            ampm = daily_match.group(3)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return ('cron', CronTrigger(hour=hour, minute=minute))
        
        # "tomorrow at HH:MM" pattern
        tomorrow_match = re.match(r'tomorrow\s+at\s+(\d{1,2}):?(\d{2})?(?:\s*(am|pm))?', schedule_lower)
        if tomorrow_match:
            hour = int(tomorrow_match.group(1))
            minute = int(tomorrow_match.group(2) or 0)
            ampm = tomorrow_match.group(3)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            tomorrow = datetime.now() + timedelta(days=1)
            run_time = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return ('date', DateTrigger(run_date=run_time))
        
        # Default: try to parse as time for today/tomorrow
        time_match = re.match(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', schedule_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            run_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if run_time < datetime.now():
                run_time += timedelta(days=1)
            
            return ('date', DateTrigger(run_date=run_time))
        
        # Default to 1 minute from now if can't parse
        return ('date', DateTrigger(run_date=datetime.now() + timedelta(minutes=1)))
    
    async def schedule_task(
        self, 
        task_id: str,
        description: str, 
        schedule: str,
        action: Callable
    ) -> dict:
        """Schedule a new task"""
        self._ensure_started()
        
        if not self.scheduler:
            return {
                "task_id": task_id,
                "description": description,
                "next_run": None,
                "status": "error - scheduler not available"
            }
        
        trigger_type, trigger = self._parse_schedule(schedule)
        
        # Add job to scheduler
        job = self.scheduler.add_job(
            action,
            trigger=trigger,
            id=task_id,
            replace_existing=True
        )
        
        # Store metadata
        self.tasks[task_id] = {
            "description": description,
            "schedule": schedule,
            "trigger_type": trigger_type,
            "next_run": str(job.next_run_time),
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }
        
        return {
            "task_id": task_id,
            "description": description,
            "next_run": str(job.next_run_time),
            "status": "scheduled"
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if not self.scheduler:
            return False
        try:
            self.scheduler.remove_job(task_id)
            if task_id in self.tasks:
                del self.tasks[task_id]
            return True
        except Exception:
            return False
    
    def list_tasks(self) -> list:
        """List all scheduled tasks"""
        if not self.scheduler:
            return []
        result = []
        for job in self.scheduler.get_jobs():
            task_meta = self.tasks.get(job.id, {})
            result.append({
                "task_id": job.id,
                "description": task_meta.get("description", "Unknown"),
                "schedule": task_meta.get("schedule", "Unknown"),
                "next_run": str(job.next_run_time),
                "enabled": task_meta.get("enabled", True)
            })
        return result
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a task"""
        if not self.scheduler:
            return False
        try:
            self.scheduler.pause_job(task_id)
            if task_id in self.tasks:
                self.tasks[task_id]["enabled"] = False
            return True
        except Exception:
            return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if not self.scheduler:
            return False
        try:
            self.scheduler.resume_job(task_id)
            if task_id in self.tasks:
                self.tasks[task_id]["enabled"] = True
            return True
        except Exception:
            return False
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
