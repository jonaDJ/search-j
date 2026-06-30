from __future__ import annotations

from pathlib import Path
import html, zipfile

TRACKER_COLUMNS = ["Company", "Job Title", "Status", "Applied Date", "Resume Used", "Follow-Up Date", "Notes"]

def _jobs_rows(rows):
    return [["Job ID", "First Seen", "Last Seen", "Company", "Title", "Match", "Status", "Link"], *[[r["unique_id"], r["first_seen_at"], r["last_seen_at"], r["company"], r["title"], r["match_score"], r["status"], r["application_url"]] for r in rows]]

def _matches_rows(rows):
    return [["First Seen", "Company", "Job Title", "Location", "Posted Date", "Match", "Recommendation", "Missing Skills", "Application Link"], *[[r["first_seen_at"], r["company"], r["title"], r["location"], r["posted_date"], r["match_score"], r["recommendation"], r["missing_skills"], r["application_url"]] for r in rows]]

def _history_rows(rows):
    return [["Run Time", "Sources Checked", "Jobs Found", "New Jobs", "Strong Matches", "Errors"], *[[r["run_time"], r["sources_checked"], r["jobs_found"], r["new_jobs"], r["strong_matches"], r["errors"]] for r in rows]]

def _write_minimal_xlsx(path: Path, sheets: dict[str, list[list[object]]]) -> None:
    # Minimal valid OOXML workbook fallback for environments where pandas/openpyxl are unavailable.
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' + ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets)+1)) + '</Types>'
    root_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    workbook = '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + ''.join(f'<sheet name="{html.escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, name in enumerate(sheets, 1)) + '</sheets></workbook>'
    wb_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets)+1)) + '</Relationships>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types); z.writestr("_rels/.rels", root_rels); z.writestr("xl/workbook.xml", workbook); z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        for i, rows in enumerate(sheets.values(), 1):
            xml_rows = []
            for r_idx, row in enumerate(rows, 1):
                cells = ''.join(f'<c r="{chr(64+c_idx)}{r_idx}" t="inlineStr"><is><t>{html.escape(str(value or ""))}</t></is></c>' for c_idx, value in enumerate(row, 1))
                xml_rows.append(f'<row r="{r_idx}">{cells}</row>')
            z.writestr(f"xl/worksheets/sheet{i}.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(xml_rows) + '</sheetData></worksheet>')

def export_workbook(path: Path, new_matches, all_jobs, run_history) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sheets = {"New_Matches": _matches_rows(new_matches), "All_Jobs": _jobs_rows(all_jobs), "Application_Tracker": [TRACKER_COLUMNS], "Run_History": _history_rows(run_history)}
    try:
        import pandas as pd
        from openpyxl import load_workbook
    except ModuleNotFoundError:
        _write_minimal_xlsx(path, sheets)
        return
    tracker = pd.DataFrame(columns=TRACKER_COLUMNS)
    if path.exists():
        try: tracker = pd.read_excel(path, sheet_name="Application_Tracker")
        except ValueError: pass
    for col in TRACKER_COLUMNS:
        if col not in tracker.columns: tracker[col] = ""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(sheets["New_Matches"][1:], columns=sheets["New_Matches"][0]).to_excel(writer, sheet_name="New_Matches", index=False)
        pd.DataFrame(sheets["All_Jobs"][1:], columns=sheets["All_Jobs"][0]).to_excel(writer, sheet_name="All_Jobs", index=False)
        tracker[TRACKER_COLUMNS].to_excel(writer, sheet_name="Application_Tracker", index=False)
        pd.DataFrame(sheets["Run_History"][1:], columns=sheets["Run_History"][0]).to_excel(writer, sheet_name="Run_History", index=False)
    wb = load_workbook(path)
    for ws in wb.worksheets: ws.freeze_panes = "A2"
    wb.save(path)
