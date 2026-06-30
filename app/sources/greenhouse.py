from __future__ import annotations

from datetime import datetime, timezone
import httpx
from app.models import JobPosting, CompanySource

async def fetch_greenhouse(source: CompanySource, client: httpx.AsyncClient) -> list[JobPosting]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{source.board_identifier}/jobs?content=true"
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()
    jobs = []
    for item in data.get("jobs", []):
        offices = item.get("offices") or []
        location = item.get("location", {}).get("name") or ", ".join(o.get("name", "") for o in offices)
        posted = item.get("updated_at") or item.get("created_at")
        posted_date = datetime.fromisoformat(posted.replace("Z", "+00:00")).date() if posted else None
        jobs.append(JobPosting(source="greenhouse", source_job_id=str(item.get("id")) if item.get("id") else None, company=source.company, title=item.get("title", ""), location=location or "", description=item.get("content") or "", posted_date=posted_date, application_url=item.get("absolute_url") or item.get("internal_job_id", ""), retrieved_at=datetime.now(timezone.utc)))
    return jobs
