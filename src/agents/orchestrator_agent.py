import logging
from typing import List
from src.agents.search_agent import SearchAgent
from src.agents.profile_agent import ProfileAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.notification_agent import NotificationAgent
from src.storage.db import JobDatabase
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Coordinates the full agentic workflow: Fetch -> Rank -> Persist -> Notify."""
    
    def __init__(
        self,
        search_agent: SearchAgent,
        profile_agent: ProfileAgent,
        ranking_agent: RankingAgent,
        notification_agent: NotificationAgent,
        db: JobDatabase,
        settings: Settings,
        job_fit_agent = None,
        enable_llm_reasoning: bool = False
    ):
        self.search_agent = search_agent
        self.profile_agent = profile_agent
        self.ranking_agent = ranking_agent
        self.notification_agent = notification_agent
        self.db = db
        self.settings = settings
        self.job_fit_agent = job_fit_agent
        self.enable_llm_reasoning = enable_llm_reasoning
        
    def execute_workflow(self) -> bool:
        """Runs the coordinated job scouting loop."""
        logger.info("OrchestratorAgent starting workflow execution...")
        
        # 1. Load Profile
        profile = self.profile_agent.load_profile()
        min_score = profile.minimum_match_score
        
        # 2. Collect Jobs
        jobs = self.search_agent.collect_jobs(limit=50)
        
        # 3. Rank Jobs
        ranked_results = self.ranking_agent.rank(jobs)
        
        # 4. Filter
        self.matched_jobs = []
        self.rejected_jobs = []
        for job, score, matches in ranked_results:
            if score >= min_score:
                self.matched_jobs.append(job)
            else:
                self.rejected_jobs.append(job)
                
        # Optional: Run JobFitAgent LLM analysis if enabled
        if self.enable_llm_reasoning and self.job_fit_agent:
            logger.info("Running optional JobFitAgent LLM-based reasoning for matched jobs...")
            self.job_fit_agent.enable_llm_reasoning = self.enable_llm_reasoning
            for job in self.matched_jobs:
                fit_result = self.job_fit_agent.analyze_fit(job, profile)
                if not job.extracted_metadata:
                    job.extracted_metadata = {}
                job.extracted_metadata["fit_analysis"] = fit_result.model_dump()
                logger.info(f"Fit analysis for {job.title}: {fit_result.fit_summary}")
                
        # 5. Persist
        saved_count = 0
        for job in self.matched_jobs:
            if self.db.save_job(job):
                saved_count += 1
        logger.info(f"OrchestratorAgent saved {saved_count} matched jobs.")
        
        # 6. Notify
        summary = self.notification_agent.notify_summary(self.matched_jobs)
        logger.info(f"\n{summary}")
        
        return True

