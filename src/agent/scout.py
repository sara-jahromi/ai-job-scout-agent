import logging
from src.config.settings import Settings
from src.config.profile import UserProfile, load_user_profile

from src.sources.sample_source import SampleJobSource
from src.ranking.matcher import JobMatcher
from src.storage.db import JobDatabase
from src.notifications.notifier import JobNotifier

logger = logging.getLogger(__name__)

class JobScoutAgent:
    """Core Agent that orchestrates the job search, extraction, ranking, and notification process."""
    
    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self._setup_logging()
        logger.info("Initializing AI Job Scout Agent...")
        
        # Load and validate user matching criteria profile
        logger.info(f"Loading user profile from: {self.settings.user_profile_path}")
        self.profile = load_user_profile(self.settings.user_profile_path)
        logger.info("User profile loaded and validated successfully.")
        
        # Initialize loaded state
        self.fetched_jobs = []
        self.ranked_jobs = []
        self.matched_jobs = []
        self.rejected_jobs = []
        
    def _setup_logging(self):
        logging.basicConfig(
            level=self.settings.LOG_LEVEL,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
    def run(self):
        """Orchestrate one run loop of the scout agent."""
        logger.info("AI Job Scout Agent starting pipeline execution.")
        
        # 1. Fetch job postings from sources
        logger.info("Step 1: Fetching job postings from SampleJobSource...")
        source = SampleJobSource(self.settings.sample_jobs_path)
        jobs = source.search_jobs()
        self.fetched_jobs = jobs
        logger.info(f"Loaded {len(jobs)} job postings.")
        
        for idx, job in enumerate(jobs, 1):
            logger.info(f"  Job #{idx}: {job.title} at {job.company} ({job.location})")
        
        # 2. Extract structured information
        logger.info("Step 2: Extracting job metadata (Stubbed)...")
        
        # 3. Rank jobs based on user profile
        logger.info("Step 3: Ranking jobs based on user profile...")
        matcher = JobMatcher(self.profile)
        ranked_results = matcher.rank_jobs(jobs)
        self.ranked_jobs = ranked_results
        
        logger.info(f"Ranked {len(ranked_results)} jobs:")
        for idx, (job, score, matches) in enumerate(ranked_results, 1):
            logger.info(f"  [{score:.2f}] #{idx}: {job.title} at {job.company} (Matches: {', '.join(matches)})")
            
        # Filter jobs based on minimum match score
        min_score = self.profile.minimum_match_score
        self.matched_jobs = [job for job, score, matches in ranked_results if score >= min_score]
        self.rejected_jobs = [job for job, score, matches in ranked_results if score < min_score]
        
        logger.info("--- Matching Summary ---")
        logger.info(f"Total Jobs Loaded: {len(jobs)}")
        logger.info(f"Matched Jobs Count: {len(self.matched_jobs)}")
        logger.info(f"Rejected Jobs Count: {len(self.rejected_jobs)}")
        logger.info("Matched Job Listings:")
        for job in self.matched_jobs:
            logger.info(f"  [{job.match_score:.2f}] {job.title} at {job.company}")
        logger.info("------------------------")
        
        # 4. Save to storage
        logger.info("Step 4: Persisting matched results to SQLite database...")
        db = JobDatabase(self.settings.db_path)
        saved_count = 0
        for job in self.matched_jobs:
            if db.save_job(job):
                saved_count += 1
        logger.info(f"Saved {saved_count} new matched jobs to the database (out of {len(self.matched_jobs)} matched).")
        
        # 5. Send notifications
        logger.info("Step 5: Generating notification summary...")
        notifier = JobNotifier()
        summary = notifier.summarize_matches(self.matched_jobs)
        logger.info(f"\n{summary}")
        
        logger.info("Pipeline executed successfully.")
        return True
