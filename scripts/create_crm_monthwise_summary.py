
import subprocess
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

START_DATE = "2025-12-08"
END_DATE = "2026-07-10"
OUTPUT = Path("CRM_Month_Wise_Customization_Summary.xlsx")

AREAS = [
    ("Lead", ("lead",)),
    ("Project", ("project_", "project ", "spc_single_project_tracker")),
    ("Firm Name", ("firm_name", "firm name")),
    ("Segment", ("segment",)),
    ("Scope of Work", ("scope_of_work", "scope of work")),
    ("System", ("system_spc", "system_items", "system ")),
    ("Child Tables", ("child_table", "project_items", "project_details_items", "contact_person_spc", "task_multi_select_table", "crm_multi_", "select_multi_department")),
    ("Task tab development on Lead", ("crm_task", "crm_request_approvel", "task_dashboard", "task_tracker", "task_department", "task tab", "task")),
    ("Quotation", ("quotation",)),
    ("Analytics Report", ("analyatics", "analytics")),
    ("Forecast Report", ("forcast", "forecast")),
    ("SPC Single Project Tracker", ("spc_single_project_tracker",)),
    ("SPC Lead Dashboard", ("spc_lead_dashboard",)),
    ("Task Dashboard", ("task_dashboard",)),
    ("Quotation Print Format", ("print format", "best regards", "quotation print")),
]

CRM_PATH_TERMS = tuple(term for _, terms in AREAS for term in terms) + ("crm", "customer", "contact_person")


def run_git(args):
    return subprocess.check_output(["git", *args], text=True)


def parse_commits():
    raw = run_git([
        "log",
        f"--since={START_DATE}",
        f"--until={END_DATE} 23:59:59",
        "--no-merges",
        "--date=short",
        "--pretty=format:--COMMIT--%x1f%H%x1f%ad%x1f%an%x1f%s",
        "--name-only",
    ])
    commits = []
    current = None
    for line in raw.splitlines():
        if line.startswith("--COMMIT--"):
            if current:
                commits.append(current)
            _, h, d, author, subject = line.split("\x1f", 4)
            current = {"hash": h, "date": d, "author": author, "subject": subject, "files": []}
        elif current and line.strip():
            current["files"].append(line.strip())
    if current:
        commits.append(current)
    return [c for c in commits if is_relevant(c)]


def is_relevant(commit):
    text = " ".join([commit["subject"], *commit["files"]]).lower()
    return any(term in text for term in CRM_PATH_TERMS)


def detect_areas(commit):
    text = " ".join([commit["subject"], *commit["files"]]).lower()
    found = []
    for name, terms in AREAS:
        if any(term in text for term in terms):
            found.append(name)
    return found or ["CRM Module"]


def summarize_change(areas):
    parts = []
    if "Lead" in areas:
        parts.append("Lead customization")
    if "Task tab development on Lead" in areas:
        parts.append("task tab / task workflow on Lead")
    if "Project" in areas:
        parts.append("Project related fields/doctypes")
    if "Firm Name" in areas:
        parts.append("Firm Name master")
    if "Segment" in areas:
        parts.append("Segment master")
    if "Scope of Work" in areas:
        parts.append("Scope of Work master")
    if "System" in areas:
        parts.append("System master")
    if "Child Tables" in areas:
        parts.append("child tables")
    if "Quotation" in areas:
        parts.append("Quotation customization")
    if "Quotation Print Format" in areas:
        parts.append("Quotation print format")
    if "Analytics Report" in areas:
        parts.append("Analytics report")
    if "Forecast Report" in areas:
        parts.append("Forecast report")
    if "SPC Single Project Tracker" in areas:
        parts.append("SPC Single Project Tracker page")
    if "SPC Lead Dashboard" in areas:
        parts.append("SPC Lead Dashboard page")
    if "Task Dashboard" in areas:
        parts.append("Task Dashboard page")
    return ", ".join(dict.fromkeys(parts)) or ", ".join(areas)


def sheet_xml(rows):
    xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    xml.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>')
    for r_idx, row in enumerate(rows, 1):
        xml.append(f'<row r="{r_idx}">')
        for c_idx, value in enumerate(row, 1):
            col = ""
            n = c_idx
            while n:
                n, rem = divmod(n - 1, 26)
                col = chr(65 + rem) + col
            ref = f"{col}{r_idx}"
            text = escape(str(value))
            xml.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        xml.append('</row>')
    xml.append('</sheetData></worksheet>')
    return ''.join(xml)


def write_xlsx(sheets):
    sheet_count = len(sheets)
    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
    workbook_sheets = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
    workbook_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i, name in enumerate(sheets, 1):
        content_types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        workbook_sheets.append(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>')
        workbook_rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
    content_types.append('</Types>')
    workbook_sheets.append('</sheets></workbook>')
    workbook_rels.append('</Relationships>')
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', ''.join(content_types))
        zf.writestr('_rels/.rels', root_rels)
        zf.writestr('xl/workbook.xml', ''.join(workbook_sheets))
        zf.writestr('xl/_rels/workbook.xml.rels', ''.join(workbook_rels))
        for i, rows in enumerate(sheets.values(), 1):
            zf.writestr(f'xl/worksheets/sheet{i}.xml', sheet_xml(rows))


def main():
    commits = parse_commits()
    by_day = defaultdict(lambda: {"areas": set(), "changes": []})
    by_month = defaultdict(lambda: {"days": set(), "areas": set(), "changes": []})
    for c in commits:
        d = date.fromisoformat(c["date"])
        month = d.strftime("%B %Y")
        areas = detect_areas(c)
        summary = summarize_change(areas)
        by_day[c["date"]]["areas"].update(areas)
        by_day[c["date"]]["changes"].append(summary)
        by_month[month]["days"].add(c["date"])
        by_month[month]["areas"].update(areas)
        by_month[month]["changes"].append(summary)

    month_rows = [["Month", "Date", "Day", "Customization Areas", "What Changed"]]
    for month in sorted(by_month, key=lambda m: date.strptime(m, "%B %Y")):
        for day in sorted(by_month[month]["days"]):
            d = date.fromisoformat(day)
            data = by_day[day]
            month_rows.append([
                month,
                day,
                d.strftime("%A"),
                ", ".join(sorted(data["areas"])),
                "; ".join(dict.fromkeys(data["changes"])),
            ])

    day_rows = [["Month", "Date", "Day", "Customization Areas", "What Changed"]]
    for day in sorted(by_day):
        d = date.fromisoformat(day)
        data = by_day[day]
        day_rows.append([
            d.strftime("%B %Y"),
            day,
            d.strftime("%A"),
            ", ".join(sorted(data["areas"])),
            "; ".join(dict.fromkeys(data["changes"])),
        ])

    area_rows = [["Customization Area", "Dates", "Month", "Short Details"]]
    area_dates = defaultdict(set)
    area_changes = defaultdict(list)
    for day, data in by_day.items():
        d = date.fromisoformat(day)
        for area in data["areas"]:
            area_dates[area].add(day)
            area_changes[area].append(f"{d.strftime('%b %Y')}: {'; '.join(dict.fromkeys(data['changes']))}")
    for area in sorted(area_dates):
        months = sorted({date.fromisoformat(x).strftime("%B %Y") for x in area_dates[area]}, key=lambda m: date.strptime(m, "%B %Y"))
        area_rows.append([
            area,
            "\n".join(sorted(area_dates[area])),
            ", ".join(months),
            "; ".join(dict.fromkeys(area_changes[area])),
        ])

    write_xlsx({
        "Month Wise Summary": month_rows,
        "Day Wise Changes": day_rows,
        "Area Wise Summary": area_rows,
    })
    print(f"Wrote {OUTPUT}")
    print(f"Days: {len(by_day)}")
    print(f"Months: {len(by_month)}")

if __name__ == "__main__":
    main()
