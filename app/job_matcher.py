from __future__ import annotations

import re
from datetime import date
from .models import CandidateProfile, JobPosting, MatchResult

US_TERMS = ("united states", "usa", "u.s.", "us", "remote", "detroit", "mi")

def _contains_any(text: str, terms: list[str]) -> bool:
    low = text.lower()
    return any(t.lower() in low for t in terms)

def required_years(description: str) -> int | None:
    nums = [int(n) for n in re.findall(r"(\d+)\+?\s*(?:years|yrs)", description.lower())]
    return max(nums) if nums else None

def passes_basic_filters(job: JobPosting, profile: CandidateProfile, today: date | None = None) -> tuple[bool, str]:
    today = today or date.today()
    title = job.title.lower()
    if _contains_any(title, profile.excluded_titles):
        return False, "excluded title"
    if not _contains_any(title, profile.target_roles):
        return False, "unrelated title"
    if job.posted_date and (today - job.posted_date).days > profile.maximum_posting_age_days:
        return False, "posting too old"
    loc = job.location.lower()
    if not any(term in loc for term in US_TERMS):
        return False, "non-US location"
    years = required_years(job.description)
    if years is not None and years > profile.years_experience + 2:
        return False, "experience too high"
    if not job.application_url:
        return False, "missing application link"
    return True, "accepted"

def score_job(job: JobPosting, profile: CandidateProfile, today: date | None = None) -> MatchResult:
    today = today or date.today()
    text = f"{job.title} {job.description} {job.location}".lower()
    title_score = 20 if _contains_any(job.title, profile.target_roles) else 0
    matching = [s for s in profile.skills if s.lower() in text]
    missing = [s for s in profile.skills if s.lower() not in text]
    skill_score = round(30 * (len(matching) / max(1, len(profile.skills))))
    years = required_years(job.description)
    exp_match = years is None or years <= profile.years_experience + 1
    exp_score = 20 if exp_match else 0
    sf_terms = [s for s in profile.skills if "salesforce" in s.lower() or s.lower() in {"apex", "flow builder", "marketing cloud"}]
    sf_hits = [s for s in sf_terms if s.lower() in text]
    product_score = round(10 * (len(sf_hits) / max(1, len(sf_terms))))
    loc_match = any(l.lower() in text for l in profile.locations) or any(t in job.location.lower() for t in US_TERMS)
    loc_score = 10 if loc_match else 0
    sponsorship_risk = "Unknown"
    sponsor_score = 5
    if "without sponsorship" in text or "no sponsorship" in text:
        sponsorship_risk = "High"
        sponsor_score = 0 if profile.requires_future_sponsorship else 5
    fresh_score = 5 if not job.posted_date or (today - job.posted_date).days <= profile.maximum_posting_age_days else 0
    score = min(100, title_score + skill_score + exp_score + product_score + loc_score + sponsor_score + fresh_score)
    return MatchResult(match_score=score, recommendation="Apply" if score >= profile.minimum_match_score else "Review", matching_skills=matching, missing_skills=missing, experience_match=exp_match, location_match=loc_match, sponsorship_risk=sponsorship_risk, reason=f"Matched {len(matching)} skills; score {score}.")
