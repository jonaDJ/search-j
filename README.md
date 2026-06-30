# job-finder

Local Python application that checks public company job feeds, stores every encountered job in SQLite, deduplicates repeat postings, scores relevant jobs deterministically, and exports `data/jobs.xlsx` for review.

## Requirements

- Python 3.12+
- macOS, Linux, or Windows for development; scheduling instructions below target macOS `launchd`.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit:

- `data/profile.json` for your target roles, skills, locations, sponsorship needs, and filters.
- `data/companies.csv` for enabled Greenhouse and Lever boards.

## Run

```bash
python -m app.main
```

Dry run without changing `data/jobs.db` or `data/jobs.xlsx`:

```bash
python -m app.main --dry-run
```

## Outputs

- `data/jobs.db`: permanent SQLite memory of every job encountered.
- `data/jobs.xlsx`: workbook with `New_Matches`, `All_Jobs`, `Application_Tracker`, and `Run_History` sheets.

`New_Matches` only contains strong matches first discovered in the latest non-dry run. `Application_Tracker` is preserved when the workbook is regenerated.

## macOS launchd schedule

Create `~/Library/LaunchAgents/com.local.job-finder.plist` and update paths to your checkout and Python executable:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.local.job-finder</string>
  <key>WorkingDirectory</key><string>/path/to/job-finder</string>
  <key>ProgramArguments</key>
  <array><string>/path/to/job-finder/.venv/bin/python</string><string>-m</string><string>app.main</string></array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>12</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>16</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Hour</key><integer>20</integer><key>Minute</key><integer>0</integer></dict>
  </array>
  <key>StandardOutPath</key><string>/tmp/job-finder.out.log</string>
  <key>StandardErrorPath</key><string>/tmp/job-finder.err.log</string>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.local.job-finder.plist
```

## Tests

```bash
pytest
```

## Notes

This project intentionally does not submit job applications and does not scrape LinkedIn, Indeed, or other sites that block automated access. It begins with structured public ATS feeds and deterministic matching; LLM-based scoring and email delivery can be added later.
