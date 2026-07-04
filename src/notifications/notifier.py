import logging
from typing import List
from src.sources.base import JobPosting

logger = logging.getLogger(__name__)

class JobNotifier:
    """Dispatches notifications (e.g. CLI, Email, Slack) for high-match job postings."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def send_notification(self, job: JobPosting, match_score: float) -> bool:
        """Sends a notification about a matching job posting."""
        message = f"🔔 High Match Job Found: {job.title} at {job.company} (Match Score: {match_score:.2f}) - {job.url}"
        logger.info(f"Notification Sent: {message}")
        return True
        
    def summarize_matches(self, matched_jobs: List[JobPosting]) -> str:
        """Returns a readable text summary of matched jobs."""
        if not matched_jobs:
            return "No matched jobs found."
            
        lines = [
            "==================================================",
            "📢 AI JOB SCOUT: NEW MATCHES FOUND!",
            "=================================================="
        ]
        for idx, job in enumerate(matched_jobs, 1):
            score_val = job.match_score if job.match_score is not None else 0.0
            lines.append(
                f"{idx}. {job.title} at {job.company}\n"
                f"   📍 Location: {job.location}\n"
                f"   📊 Match Score: {score_val:.2f}\n"
                f"   🔗 Link: {job.url}\n"
            )
        lines.append("==================================================")
        return "\n".join(lines)
