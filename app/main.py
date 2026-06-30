from __future__ import annotations

import argparse, asyncio, logging
import httpx
from .config import load_profile, load_companies, DB_PATH, EXCEL_PATH, TIMEOUT_SECONDS
from .database import JobDatabase
from .duplicate_checker import attach_identifiers
from .excel_exporter import export_workbook
from .job_matcher import passes_basic_filters, score_job
from .sources import fetch_greenhouse, fetch_lever, fetch_direct

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
FETCHERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever, "direct": fetch_direct}

async def collect(companies):
    errors, jobs = [], []
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
        for source in [c for c in companies if c.enabled]:
            try:
                fetched = await FETCHERS[source.ats](source, client)
                jobs.extend(attach_identifiers(j) for j in fetched)
            except Exception as exc:
                msg = f"{source.company} ({source.ats}) failed: {exc}"
                logging.warning(msg)
                errors.append(msg)
    return jobs, errors

def run(dry_run: bool = False) -> int:
    profile = load_profile()
    companies = load_companies()
    enabled = [c for c in companies if c.enabled]
    jobs, errors = asyncio.run(collect(companies))
    db = JobDatabase(DB_PATH)
    new_ids, strong = [], 0
    try:
        for job in jobs:
            accepted, _ = passes_basic_filters(job, profile)
            match = score_job(job, profile) if accepted else None
            if match and match.match_score >= profile.minimum_match_score:
                strong += 1
            if not dry_run:
                is_new = db.upsert_job(job, match)
                if is_new and match and match.match_score >= profile.minimum_match_score:
                    new_ids.append(job.unique_id or "")
        if not dry_run:
            db.add_run(len(enabled), len(jobs), len(new_ids), len(new_ids), errors)
            export_workbook(EXCEL_PATH, db.jobs_by_ids(new_ids), db.all_jobs(), db.run_history())
        logging.info("sources=%s found=%s new_matches=%s dry_run=%s", len(enabled), len(jobs), len(new_ids), dry_run)
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find new matching jobs from public ATS boards.")
    parser.add_argument("--dry-run", action="store_true", help="Retrieve and analyze without changing SQLite or Excel outputs.")
    raise SystemExit(run(parser.parse_args().dry_run))
