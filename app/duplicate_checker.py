from __future__ import annotations

import hashlib, re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from .models import JobPosting

TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"gh_src", "lever-source", "src", "source"}

def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())

def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith(TRACKING_PREFIXES) and k.lower() not in TRACKING_PARAMS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))

def make_unique_id(job: JobPosting) -> str:
    if job.source_job_id:
        return f"{job.source.lower()}:{job.source_job_id}"
    return make_fingerprint(job)

def make_fingerprint(job: JobPosting) -> str:
    raw = "|".join([normalize_text(job.company), normalize_text(job.title), normalize_text(job.location), canonical_url(job.application_url)])
    return hashlib.sha256(raw.encode()).hexdigest()

def attach_identifiers(job: JobPosting) -> JobPosting:
    job.fingerprint = make_fingerprint(job)
    job.unique_id = make_unique_id(job)
    return job
