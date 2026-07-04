import sqlite3
import json
import uuid
from typing import List, Optional
from pathlib import Path
from src.sources.base import JobPosting

class JobDatabase:
    """Manages the persistence of job postings using SQLite."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize database tables if they do not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    remote INTEGER DEFAULT 0,
                    url TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    required_skills TEXT,
                    posted_date TEXT,
                    match_score REAL DEFAULT 0.0,
                    saved_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
    def save_job(self, job: JobPosting) -> bool:
        """
        Saves a job posting to the database. Avoids duplicates by url.
        
        Returns:
            True if the job was newly saved, False if it was skipped (already exists).
        """
        required_skills = []
        remote = 0
        if job.extracted_metadata:
            required_skills = job.extracted_metadata.get("required_skills", [])
            remote_val = job.extracted_metadata.get("remote", False)
            remote = 1 if remote_val else 0
            
        skills_json = json.dumps(required_skills)
        job_id = job.id or str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO jobs (
                    id, title, company, location, remote, url, description, required_skills, posted_date, match_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                job.title,
                job.company,
                job.location,
                remote,
                job.url,
                job.description,
                skills_json,
                job.posted_date,
                job.match_score
            ))
            conn.commit()
            return cursor.rowcount > 0
        
    def get_jobs(self, limit: int = 50) -> List[JobPosting]:
        """Retrieves saved job postings from the database sorted by match score."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, title, company, location, remote, url, description, required_skills, posted_date, match_score, saved_at
                FROM jobs
                ORDER BY match_score DESC
                LIMIT ?
            """, (limit,))
            
            postings = []
            for row in cursor.fetchall():
                required_skills = []
                if row["required_skills"]:
                    try:
                        required_skills = json.loads(row["required_skills"])
                    except Exception:
                        pass
                
                postings.append(JobPosting(
                    id=row["id"],
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    url=row["url"],
                    description=row["description"],
                    source="SQLite",
                    posted_date=row["posted_date"],
                    match_score=row["match_score"],
                    extracted_metadata={
                        "required_skills": required_skills,
                        "remote": bool(row["remote"]),
                        "saved_at": row["saved_at"]
                    }
                ))
            return postings
