import csv
import html
import subprocess
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape


START_DATE = "2025-12-08"
END_DATE = "2026-07-10"
HOURLY_RATE = 1000
OUTPUT = Path("CRM_Customization_Report_2025-12-08_to_2026-07-10.xlsx")

CRM_TERMS = (
    "crm",
    "lead",
    "quotation",
    "customer",
    "opportunity",
    "sales_order",
    "sales order",
    "sales_invoice",
    "sales invoice",
    "forecast",
    "forcast",
    "proforma",
    "task_dashboard",
    "spc_lead_dashboard",
    "spc_single_project_tracker",
    "accounts_receivable",
    "contact_person",
    "firm_name",
    "scope_of_work",
    "segment",
    "project_items",
    "project_details",
)

NEW_DOCTYPE_HINTS = (
    "crm_multi_assign_to_user",
    "crm_multi_department_select",
    "crm_request_approvel",
    "crm_task",
    "select_multi_department",
    "contact_person_spc",
    "firm_name_spc",
    "firm_type",
    "firm_type_items",
    "other_contact_person",
    "scope_of_work",
    "segment",
    "system_spc",
    "system_items_spc",
    "project_items",
    "project_details_items",
    "lead_person_base",
    "project_base",
    "project_person",
    "project_work",
    "proforma_invoice",
    "proforma_invoice_item",
)

PAGE_HINTS = ("spc_lead_dashboard", "spc_single_project_tracker", "task_dashboard", "sales_order_monitor")
REPORT_HINTS = (
    "forcast",
    "accounts_receivable",
    "task_tracker",
    "task_department_wise_tracker",
    "analyatics",
    "item_price_spc",
    "sales_order_analysis_spc",
)


def run_git(args):
    return subprocess.check_output(["git", *args], text=True)


def is_crm_related(subject, files):
    haystack = " ".join([subject, *files]).lower()
    return any(term in haystack for term in CRM_TERMS)


def classify(subject, files):
    text = " ".join([subject, *files]).lower()
    if "dashboard" in text:
        return "CRM Dashboard / Tracker"
    if "quotation" in text:
        return "Quotation Customization"
    if "task" in text:
        return "CRM Task / Approval"
    if "forecast" in text or "forcast" in text:
        return "Forecast / Sales Report"
    if "proforma" in text:
        return "Proforma Invoice"
    if "accounts_receivable" in text:
        return "Accounts Receivable Report"
    if "lead" in text:
        return "Lead Customization"
    if "customer" in text:
        return "Customer Customization"
    if "sales_order" in text or "sales order" in text or "sales_invoice" in text:
        return "Sales Flow Customization"
    return "CRM Related Customization"


def work_area(files):
    text = " ".join(files).lower()
    areas = []
    if "lead" in text:
        areas.append("Lead")
    if "quotation" in text:
        areas.append("Quotation")
    if "customer" in text:
        areas.append("Customer")
    if "crm_task" in text or "crm_request" in text or "task_dashboard" in text:
        areas.append("CRM Task / Approval")
    if any(page in text for page in PAGE_HINTS):
        areas.append("Dashboard / Page")
    if any(report in text for report in REPORT_HINTS):
        areas.append("Report")
    if "proforma_invoice" in text:
        areas.append("Proforma Invoice")
    if any(dt in text for dt in NEW_DOCTYPE_HINTS):
        areas.append("New / Custom Doctype")
    return ", ".join(dict.fromkeys(areas)) or "CRM Module"


def describe_work(subject, files):
    text = " ".join([subject, *files]).lower()
    details = []
    if "lead" in text:
        details.append("Lead form/client script/server logic customization")
    if "custom/lead.json" in text:
        details.append("Lead custom fields/properties updated")
    if "quotation" in text:
        details.append("Quotation form/custom field/print related changes")
    if "spc_lead_dashboard" in text:
        details.append("SPC Lead Dashboard created/enhanced/fixed")
    if "spc_single_project_tracker" in text:
        details.append("Single Project Tracker page added for lead/project follow-up")
    if "task_dashboard" in text:
        details.append("Task Dashboard page added")
    if "crm_task" in text or "crm_request_approvel" in text:
        details.append("CRM Task and Request Approval doctypes added")
    if "crm_multi_assign_to_user" in text or "crm_multi_department_select" in text or "select_multi_department" in text:
        details.append("Multi-user and multi-department assignment doctypes added")
    if "contact_person_spc" in text or "firm_name_spc" in text or "firm_type" in text or "other_contact_person" in text:
        details.append("Firm/contact master doctypes added or modified")
    if "scope_of_work" in text or "segment" in text or "system_spc" in text or "project_items" in text:
        details.append("Project, system, segment, scope, and item master doctypes updated")
    if "forcast" in text:
        details.append("Forecast report added/modified")
    if "accounts_receivable" in text:
        details.append("Accounts Receivable report customized")
    if "task_tracker" in text or "task_department_wise_tracker" in text:
        details.append("Task tracking reports added")
    if "proforma_invoice" in text:
        details.append("Proforma Invoice doctype/custom logic updated")
    if "followup" in text or "event" in text:
        details.append("Follow-up date/event tracking added")
    if "best regards" in text:
        details.append("Best regards field visibility adjusted")
    if not details:
        details.append(subject)
    return "; ".join(dict.fromkeys(details))


def file_type(path):
    p = path.lower()
    if "/doctype/" in p:
        return "Doctype"
    if "/page/" in p:
        return "Dashboard / Page"
    if "/report/" in p:
        return "Report"
    if "/custom/" in p:
        return "Custom Field / Property"
    if "/public/js/" in p:
        return "Client Script"
    if "/public/py/" in p or p.endswith(".py"):
        return "Server Script"
    if p.startswith("docs/"):
        return "Documentation / Mockup"
    if p.endswith(".json"):
        return "JSON Metadata"
    return "Other"


def estimate_hours(files, insertions, deletions, subject):
    relevant_files = [f for f in files if is_crm_related(subject, [f])]
    file_count = len(relevant_files) or len(files)
    churn = insertions + deletions
    hours = 0.75 + file_count * 0.45 + min(churn / 180.0, 5.0)
    text = " ".join([subject, *files]).lower()
    if any(x in text for x in ("dashboard", "report", "doctype", "approval", "proforma")):
        hours += 1.0
    if file_count >= 8:
        hours += 1.5
    if file_count >= 18:
        hours += 2.0
    return round(max(1.0, min(hours, 12.0)) * 2) / 2


def parse_commits():
    raw = run_git([
        "log",
        f"--since={START_DATE}",
        f"--until={END_DATE} 23:59:59",
        "--no-merges",
        "--date=short",
        "--pretty=format:--COMMIT--%x1f%H%x1f%ad%x1f%an%x1f%s",
        "--numstat",
    ])
    commits = []
    current = None
    for line in raw.splitlines():
        if line.startswith("--COMMIT--"):
            if current:
                commits.append(current)
            _, commit_hash, commit_date, author, subject = line.split("\x1f", 4)
            current = {
                "hash": commit_hash,
                "date": commit_date,
                "author": author,
                "subject": subject,
                "files": [],
                "insertions": 0,
                "deletions": 0,
            }
            continue
        if not current or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            ins = 0 if parts[0] == "-" else int(parts[0])
            dels = 0 if parts[1] == "-" else int(parts[1])
            current["insertions"] += ins
            current["deletions"] += dels
            current["files"].append(parts[2])
    if current:
        commits.append(current)
    crm = []
    for commit in commits:
        if not is_crm_related(commit["subject"], commit["files"]):
            continue
        commit["category"] = classify(commit["subject"], commit["files"])
        commit["hours"] = estimate_hours(
            commit["files"],
            commit["insertions"],
            commit["deletions"],
            commit["subject"],
        )
        commit["cost"] = commit["hours"] * HOURLY_RATE
        crm.append(commit)
    return sorted(crm, key=lambda c: (c["date"], c["hash"]))


def sheet_xml(rows):
    xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    xml.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
    xml.append("<sheetData>")
    for r_idx, row in enumerate(rows, 1):
        xml.append(f'<row r="{r_idx}">')
        for c_idx, value in enumerate(row, 1):
            col = ""
            n = c_idx
            while n:
                n, rem = divmod(n - 1, 26)
                col = chr(65 + rem) + col
            ref = f"{col}{r_idx}"
            if isinstance(value, (int, float)):
                xml.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                text = escape(str(value))
                xml.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        xml.append("</row>")
    xml.append("</sheetData></worksheet>")
    return "".join(xml)


def workbook_xml(sheet_names):
    sheets = []
    for i, name in enumerate(sheet_names, 1):
        sheets.append(
            f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{''.join(sheets)}</sheets></workbook>"
    )


def rels_xml(sheet_count):
    rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for i in range(1, sheet_count + 1):
        rels.append(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        )
    rels.append("</Relationships>")
    return "".join(rels)


def content_types_xml(sheet_count):
    overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    ]
    for i in range(1, sheet_count + 1):
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{''.join(overrides)}</Types>"
    )


def root_rels_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def write_xlsx(sheets):
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml(len(sheets)))
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("xl/workbook.xml", workbook_xml(list(sheets)))
        zf.writestr("xl/_rels/workbook.xml.rels", rels_xml(len(sheets)))
        for idx, rows in enumerate(sheets.values(), 1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_xml(rows))


def main():
    commits = parse_commits()
    day_totals = defaultdict(lambda: {"hours": 0, "cost": 0, "changes": [], "categories": set()})
    category_totals = defaultdict(lambda: {"hours": 0, "cost": 0, "commits": 0})
    detail = [[
        "Date", "Day", "Work Area", "Category", "What Was Changed", "Commit Message", "Author",
        "Estimated Hours", "Rate per Hour", "Estimated Cost", "Files Changed", "CRM File Count",
        "Insertions", "Deletions", "Commit",
    ]]
    file_rows = [["Date", "Day", "Work Area", "File Type", "File Path", "Commit Message", "Commit"]]
    lead_rows = [["Date", "Day", "What Was Changed", "Files Changed", "Estimated Hours", "Estimated Cost", "Commit"]]
    doctype_rows = [["Date", "Day", "Doctype / Folder", "What Was Changed", "Files Changed", "Estimated Hours", "Commit"]]
    dashboard_rows = [["Date", "Day", "Dashboard / Page", "What Was Changed", "Files Changed", "Estimated Hours", "Commit"]]
    report_rows = [["Date", "Day", "Report", "What Was Changed", "Files Changed", "Estimated Hours", "Commit"]]
    for c in commits:
        d = date.fromisoformat(c["date"])
        files = "\n".join(c["files"])
        crm_files = [f for f in c["files"] if is_crm_related(c["subject"], [f])]
        area = work_area(c["files"])
        description = describe_work(c["subject"], c["files"])
        detail.append([
            c["date"], d.strftime("%A"), area, c["category"], description, c["subject"], c["author"],
            c["hours"], HOURLY_RATE, c["cost"], files, len(crm_files),
            c["insertions"], c["deletions"], c["hash"][:12],
        ])
        for path in crm_files:
            file_rows.append([c["date"], d.strftime("%A"), area, file_type(path), path, c["subject"], c["hash"][:12]])
        if any("lead" in f.lower() for f in c["files"]) or "lead" in c["subject"].lower():
            lead_rows.append([c["date"], d.strftime("%A"), description, files, c["hours"], c["cost"], c["hash"][:12]])
        for hint in NEW_DOCTYPE_HINTS:
            matching = [f for f in c["files"] if hint in f.lower()]
            if matching:
                doctype_rows.append([c["date"], d.strftime("%A"), hint.replace("_", " ").title(), description, "\n".join(matching), c["hours"], c["hash"][:12]])
        for hint in PAGE_HINTS:
            matching = [f for f in c["files"] if hint in f.lower()]
            if matching:
                dashboard_rows.append([c["date"], d.strftime("%A"), hint.replace("_", " ").title(), description, "\n".join(matching), c["hours"], c["hash"][:12]])
        for hint in REPORT_HINTS:
            matching = [f for f in c["files"] if hint in f.lower()]
            if matching:
                report_rows.append([c["date"], d.strftime("%A"), hint.replace("_", " ").title(), description, "\n".join(matching), c["hours"], c["hash"][:12]])
        day_totals[c["date"]]["hours"] += c["hours"]
        day_totals[c["date"]]["cost"] += c["cost"]
        day_totals[c["date"]]["changes"].append(description)
        day_totals[c["date"]]["categories"].add(c["category"])
        category_totals[c["category"]]["hours"] += c["hours"]
        category_totals[c["category"]]["cost"] += c["cost"]
        category_totals[c["category"]]["commits"] += 1

    total_hours = round(sum(c["hours"] for c in commits), 2)
    total_cost = total_hours * HOURLY_RATE
    summary = [
        ["CRM Customization Cost Summary"],
        ["Project", "SPCON CRM Customization"],
        ["Report Period", f"{START_DATE} to {END_DATE}"],
        ["Source", "Local git history, CRM-related commits and files in spcon app"],
        ["Total CRM Commits", len(commits)],
        ["Total Estimated Hours", total_hours],
        ["Hourly Rate", HOURLY_RATE],
        ["Total Estimated Cost", total_cost],
        [],
        ["Included Main Work", "Lead customization, new CRM doctypes, dashboards/pages, reports, quotation, customer, proforma and sales-flow CRM files"],
        ["Note", "Hours are estimated from commit/file/churn complexity because no timesheet was found in the repo."],
        ["Note", "Change the Hourly Rate value and recalculate cost if your billing rate is different."],
    ]
    daily = [["Date", "Day", "Categories", "Changes Done", "Estimated Hours", "Estimated Cost"]]
    for day in sorted(day_totals):
        d = date.fromisoformat(day)
        info = day_totals[day]
        daily.append([
            day,
            d.strftime("%A"),
            ", ".join(sorted(info["categories"])),
            "\n".join(dict.fromkeys(info["changes"])),
            round(info["hours"], 2),
            round(info["cost"], 2),
        ])
    categories = [["Category", "Commits", "Estimated Hours", "Estimated Cost"]]
    for category, info in sorted(category_totals.items()):
        categories.append([category, info["commits"], round(info["hours"], 2), round(info["cost"], 2)])
    assumptions = [
        ["Assumption", "Value"],
        ["Start date interpreted as", "08/12/2025 = 8 December 2025"],
        ["End date", "10 July 2026"],
        ["Currency", "INR"],
        ["Hourly rate used", HOURLY_RATE],
        ["CRM filter terms", ", ".join(CRM_TERMS)],
        ["Focus", "Lead, CRM doctypes, dashboards/pages, reports, quotation/customer/proforma/sales CRM work"],
        ["Excluded", "Non-CRM commits; merge commits are excluded from hour totals to avoid double counting"],
        ["Estimation method", "Base hours per CRM commit plus file count, insertions/deletions, and extra weight for dashboard/report/doctype work"],
    ]
    write_xlsx({
        "Summary": summary,
        "Day Wise CRM Work": daily,
        "Detailed CRM Changes": detail,
        "Lead Work": lead_rows,
        "New Doctypes": doctype_rows,
        "Dashboards Pages": dashboard_rows,
        "Reports": report_rows,
        "CRM Files Changed": file_rows,
        "Category Summary": categories,
        "Assumptions": assumptions,
    })
    print(f"Wrote {OUTPUT}")
    print(f"CRM commits: {len(commits)}")
    print(f"Estimated hours: {total_hours}")
    print(f"Estimated cost: {total_cost}")


if __name__ == "__main__":
    main()
