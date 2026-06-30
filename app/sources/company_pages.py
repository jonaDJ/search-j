from __future__ import annotations
from app.models import CompanySource, JobPosting

async def fetch_direct(source: CompanySource, client) -> list[JobPosting]:
    # Direct career pages vary widely. This placeholder records support without scraping blocked sites.
    return []
