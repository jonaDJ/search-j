from __future__ import annotations

import csv, json, os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None
from .models import CandidateProfile, CompanySource

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

def path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else BASE_DIR / value

PROFILE_PATH = path_from_env("JOB_FINDER_PROFILE", "data/profile.json")
COMPANIES_PATH = path_from_env("JOB_FINDER_COMPANIES", "data/companies.csv")
DB_PATH = path_from_env("JOB_FINDER_DB", "data/jobs.db")
EXCEL_PATH = path_from_env("JOB_FINDER_EXCEL", "data/jobs.xlsx")
TIMEOUT_SECONDS = float(os.getenv("JOB_FINDER_TIMEOUT_SECONDS", "15"))

def load_profile(path: Path = PROFILE_PATH) -> CandidateProfile:
    return CandidateProfile.model_validate(json.loads(path.read_text()))

def load_companies(path: Path = COMPANIES_PATH) -> list[CompanySource]:
    with path.open(newline="") as f:
        rows = csv.DictReader(f)
        return [CompanySource(company=r["Company"], ats=r["ATS"], board_identifier=r["Board Identifier"], enabled=r.get("Enabled", "Yes")) for r in rows]
