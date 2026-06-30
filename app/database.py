from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from .models import JobPosting, MatchResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  unique_id TEXT PRIMARY KEY,
  fingerprint TEXT NOT NULL,
  source TEXT NOT NULL,
  source_job_id TEXT,
  company TEXT NOT NULL,
  title TEXT NOT NULL,
  location TEXT,
  description TEXT,
  posted_date TEXT,
  application_url TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  match_score INTEGER,
  recommendation TEXT,
  matching_skills TEXT,
  missing_skills TEXT,
  status TEXT DEFAULT 'New'
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(fingerprint);
CREATE TABLE IF NOT EXISTS run_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_time TEXT NOT NULL,
  sources_checked INTEGER NOT NULL,
  jobs_found INTEGER NOT NULL,
  new_jobs INTEGER NOT NULL,
  strong_matches INTEGER NOT NULL,
  errors TEXT
);
"""

class JobDatabase:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def upsert_job(self, job: JobPosting, match: MatchResult | None) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        existing = self.conn.execute("SELECT unique_id FROM jobs WHERE unique_id=? OR fingerprint=?", (job.unique_id, job.fingerprint)).fetchone()
        if existing:
            self.conn.execute("UPDATE jobs SET last_seen_at=? WHERE unique_id=?", (now, existing["unique_id"]))
            self.conn.commit()
            return False
        self.conn.execute(
            """INSERT INTO jobs (unique_id,fingerprint,source,source_job_id,company,title,location,description,posted_date,application_url,first_seen_at,last_seen_at,match_score,recommendation,matching_skills,missing_skills)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (job.unique_id, job.fingerprint, job.source, job.source_job_id, job.company, job.title, job.location, job.description, job.posted_date.isoformat() if job.posted_date else None, job.application_url, now, now, match.match_score if match else None, match.recommendation if match else None, ", ".join(match.matching_skills) if match else "", ", ".join(match.missing_skills) if match else ""),
        )
        self.conn.commit()
        return True

    def all_jobs(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM jobs ORDER BY first_seen_at DESC"))

    def jobs_by_ids(self, ids: list[str]) -> list[sqlite3.Row]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        return list(self.conn.execute(f"SELECT * FROM jobs WHERE unique_id IN ({placeholders}) ORDER BY first_seen_at DESC", ids))

    def add_run(self, sources_checked: int, jobs_found: int, new_jobs: int, strong_matches: int, errors: list[str]) -> None:
        self.conn.execute("INSERT INTO run_history (run_time,sources_checked,jobs_found,new_jobs,strong_matches,errors) VALUES (?,?,?,?,?,?)", (datetime.now(timezone.utc).isoformat(), sources_checked, jobs_found, new_jobs, strong_matches, "\n".join(errors)))
        self.conn.commit()

    def run_history(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM run_history ORDER BY run_time DESC"))
