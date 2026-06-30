from datetime import date, timedelta
from pathlib import Path
from app.database import JobDatabase
from app.duplicate_checker import attach_identifiers, canonical_url
from app.excel_exporter import export_workbook
from app.job_matcher import passes_basic_filters, score_job
from app.models import CandidateProfile, JobPosting


def profile():
    return CandidateProfile(target_roles=["Salesforce Developer"], years_experience=5, skills=["Salesforce", "Apex", "REST APIs"], locations=["United States", "Remote"], employment_types=["Full-time"], requires_future_sponsorship=True, minimum_match_score=70, maximum_posting_age_days=3, excluded_titles=["Director"])


def job(source_id="123"):
    return attach_identifiers(JobPosting(source="greenhouse", source_job_id=source_id, company="Acme", title="Salesforce Developer", location="Remote - United States", description="Build Salesforce Apex integrations and REST APIs. 4 years experience.", posted_date=date.today(), application_url="https://example.com/jobs/123?utm_source=x"))


def test_canonical_url_removes_tracking():
    assert canonical_url("HTTPS://Example.com/jobs/123/?utm_source=x&ok=1") == "https://example.com/jobs/123?ok=1"


def test_duplicate_detection_updates_existing(tmp_path: Path):
    db = JobDatabase(tmp_path / "jobs.db")
    j = job()
    match = score_job(j, profile())
    assert db.upsert_job(j, match) is True
    assert db.upsert_job(j, match) is False
    assert len(db.all_jobs()) == 1
    db.close()


def test_scoring_and_filters_accept_relevant_job():
    p = profile()
    j = job()
    accepted, reason = passes_basic_filters(j, p)
    assert accepted, reason
    result = score_job(j, p)
    assert result.match_score >= 70
    assert "Apex" in result.matching_skills


def test_filters_reject_old_and_excluded_jobs():
    p = profile()
    old = job("old")
    old.posted_date = date.today() - timedelta(days=10)
    assert passes_basic_filters(old, p)[0] is False
    director = job("director")
    director.title = "Director, Salesforce Developer"
    assert passes_basic_filters(director, p)[0] is False


def test_excel_export_preserves_tracker(tmp_path: Path):
    db = JobDatabase(tmp_path / "jobs.db")
    j = job()
    m = score_job(j, profile())
    db.upsert_job(j, m)
    db.add_run(1, 1, 1, 1, [])
    xlsx = tmp_path / "jobs.xlsx"
    export_workbook(xlsx, db.all_jobs(), db.all_jobs(), db.run_history())
    assert xlsx.exists()
    import zipfile
    with zipfile.ZipFile(xlsx) as z:
        workbook = z.read("xl/workbook.xml").decode()
    for sheet in ["New_Matches", "All_Jobs", "Application_Tracker", "Run_History"]:
        assert sheet in workbook
    db.close()
