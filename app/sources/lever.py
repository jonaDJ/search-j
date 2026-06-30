from __future__ import annotations

from datetime import datetime, timezone
import httpx
from app.models import JobPosting, CompanySource

async def fetch_lever(source: CompanySource, client: httpx.AsyncClient) -> list[JobPosting]:
    url = f"https://api.lever.co/v0/postings/{source.board_identifier}?mode=json"
    response = await client.get(url)
    response.raise_for_status()
    jobs = []
    for item in response.json():
        created_ms = item.get("createdAt")
        posted_date = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc).date() if created_ms else None
        categories = item.get("categories") or {}
        description = "\n".join(str(item.get(k, "")) for k in ("description", "descriptionPlain", "additional"))
        jobs.append(JobPosting(source="lever", source_job_id=item.get("id"), company=source.company, title=item.get("text", ""), location=categories.get("location", ""), description=description, posted_date=posted_date, application_url=item.get("hostedUrl") or item.get("applyUrl") or "", retrieved_at=datetime.now(timezone.utc)))
    return jobs
