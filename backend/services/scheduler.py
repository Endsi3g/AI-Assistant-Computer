
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Manages background scheduled tasks for Jarvis.
    Uses APScheduler to run cron jobs like Daily Briefings.
    """
    
    def __init__(self, automation_service=None, memory_service=None):
        self.scheduler = AsyncIOScheduler()
        self.automation = automation_service
        self.memory = memory_service
        self._setup_jobs()
        
    def _setup_jobs(self):
        """Define the schedule for all background tasks."""
        
        # 1. Daily Briefing (Run at 8:00 AM every day)
        self.scheduler.add_job(
            self.run_daily_briefing,
            CronTrigger(hour=8, minute=0),
            id="daily_briefing",
            replace_existing=True
        )
        
        logger.info("Scheduler jobs configured.")

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler logic started.")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler logic shutdown.")

    async def run_daily_briefing(self):
        """
        The logic for the daily briefing.
        1. Get Weather (wttr.in)
        2. Get Agenda (Mock/Memory)
        3. Generate Summary
        4. (Optional) Speak it or send notification
        """
        logger.info("Running Daily Briefing...")
        
        try:
            # TODO: Integrate with ProactiveCore agents for a deep-dive summary
            # For now, we do a basic ReAct or strict check
            
            # Simple Weather Check (Mocking the call or import)
            # from tools.markx_actions import weather_report
            # weather = weather_report("New York") 
            
            briefing_text = f"Good morning! It is {datetime.now().strftime('%A, %B %d')}. System is online and running in True Jarvis Mode."
            
            print(f"\n[DAILY BRIEFING] {briefing_text}\n")
            
            # TODO: Push to frontend via WebSocket if possible, or store in memory
            if self.memory:
                await self.memory.store_memory(briefing_text, {"type": "briefing", "automated": True})
                
        except Exception as e:
            logger.error(f"Daily Briefing failed: {e}")
