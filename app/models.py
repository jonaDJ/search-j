from __future__ import annotations

from datetime import datetime, date, timezone
from dataclasses import dataclass, field
from typing import Literal

try:
    from pydantic import BaseModel, Field, field_validator
except ModuleNotFoundError:
    @dataclass
    class CandidateProfile:
        target_roles: list[str]
        years_experience: int
        skills: list[str]
        locations: list[str]
        employment_types: list[str]
        certifications: list[str] = field(default_factory=list)
        requires_future_sponsorship: bool = False
        minimum_match_score: int = 70
        maximum_posting_age_days: int = 3
        excluded_titles: list[str] = field(default_factory=list)
        @classmethod
        def model_validate(cls, data): return cls(**data)

    @dataclass
    class CompanySource:
        company: str
        ats: str
        board_identifier: str
        enabled: bool = True
        def __post_init__(self):
            self.ats = self.ats.strip().lower()
            self.enabled = str(self.enabled).strip().lower() in {"yes", "true", "1", "y", "enabled"}

    @dataclass
    class JobPosting:
        source: str
        company: str
        title: str
        application_url: str
        source_job_id: str | None = None
        location: str = ""
        description: str = ""
        posted_date: date | None = None
        retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
        unique_id: str | None = None
        fingerprint: str | None = None

    @dataclass
    class MatchResult:
        match_score: int
        recommendation: str
        experience_match: bool
        location_match: bool
        reason: str
        matching_skills: list[str] = field(default_factory=list)
        missing_skills: list[str] = field(default_factory=list)
        sponsorship_risk: str = "Unknown"
else:
    class CandidateProfile(BaseModel):
        target_roles: list[str]
        years_experience: int = Field(ge=0)
        skills: list[str]
        certifications: list[str] = []
        locations: list[str]
        employment_types: list[str]
        requires_future_sponsorship: bool = False
        minimum_match_score: int = Field(default=70, ge=0, le=100)
        maximum_posting_age_days: int = Field(default=3, ge=0)
        excluded_titles: list[str] = []

    class CompanySource(BaseModel):
        company: str
        ats: Literal["greenhouse", "lever", "direct"]
        board_identifier: str
        enabled: bool = True

        @field_validator("ats", mode="before")
        @classmethod
        def normalize_ats(cls, value: str) -> str:
            return str(value).strip().lower()

        @field_validator("enabled", mode="before")
        @classmethod
        def parse_enabled(cls, value: object) -> bool:
            return str(value).strip().lower() in {"yes", "true", "1", "y", "enabled"}

    class JobPosting(BaseModel):
        source: str
        source_job_id: str | None = None
        company: str
        title: str
        location: str = ""
        description: str = ""
        posted_date: date | None = None
        application_url: str
        retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
        unique_id: str | None = None
        fingerprint: str | None = None

    class MatchResult(BaseModel):
        match_score: int = Field(ge=0, le=100)
        recommendation: str
        matching_skills: list[str] = []
        missing_skills: list[str] = []
        experience_match: bool
        location_match: bool
        sponsorship_risk: str = "Unknown"
        reason: str
