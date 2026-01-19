from __future__ import unicode_literals

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    columns = get_columns()
    data = get_data(filters)
    return columns, data


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are required."))


def get_columns():
    return [
        {
            "label": _("Month"),
            "fieldname": "month",
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "label": _("Ledger"),
            "fieldname": "ledger_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200,
        },
        {
            "label": _("Party Type"),
            "fieldname": "party_type",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 120,
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            "width": 200,
        },
        {
            "label": _("Opening Balance"),
            "fieldname": "opening",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 130,
        },
        {
            "label": _("Debit"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120,
        },
        {
            "label": _("Credit"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 120,
        },
        {
            "label": _("Closing Balance"),
            "fieldname": "closing",
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 130,
        },
    ]


def get_data(filters):
    from_date = getdate(filters.from_date)
    to_date = getdate(filters.to_date)

    opening_rows = get_rows(filters, "gl.posting_date < %(from_date)s")
    range_rows = get_rows(filters, "gl.posting_date BETWEEN %(from_date)s AND %(to_date)s")

    opening_balances = defaultdict(float)
    for row in opening_rows:
        key = get_key(row)
        opening_balances[key] += flt(row.debit) - flt(row.credit)

    monthly_totals = defaultdict(lambda: {"debit": 0.0, "credit": 0.0})
    for row in range_rows:
        month_start = get_month_start(row.posting_date)
        key = (month_start, get_key(row))
        monthly_totals[key]["debit"] += flt(row.debit)
        monthly_totals[key]["credit"] += flt(row.credit)

    months = get_months(from_date, to_date)
    keys = set(opening_balances.keys())
    keys.update(key for _, key in monthly_totals.keys())

    data = []
    for ledger_key in sorted(keys):
        running = opening_balances.get(ledger_key, 0.0)
        for month_start in months:
            totals = monthly_totals.get((month_start, ledger_key))
            debit = totals["debit"] if totals else 0.0
            credit = totals["credit"] if totals else 0.0
            closing = running + debit - credit

            if running or debit or credit or closing:
                data.append(
                    {
                        "month": month_start.strftime("%b-%Y"),
                        "ledger_account": ledger_key[0] or None,
                        "party_type": ledger_key[1] or None,
                        "party": ledger_key[2] or None,
                        "opening": running,
                        "debit": debit,
                        "credit": credit,
                        "closing": closing,
                    }
                )

            running = closing

    return data


def get_rows(filters, date_condition):
    conditions, values = get_conditions(filters)
    values.update({"from_date": filters.from_date, "to_date": filters.to_date})

    query = f"""
        SELECT
            gl.posting_date,
            gl.account,
            gl.party_type,
            gl.party,
            COALESCE(SUM(gl.debit), 0) AS debit,
            COALESCE(SUM(gl.credit), 0) AS credit
        FROM `tabGL Entry` gl
        WHERE {conditions}
            AND {date_condition}
        GROUP BY
            gl.posting_date,
            gl.account,
            gl.party_type,
            gl.party
    """
    return frappe.db.sql(query, values, as_dict=True)


def get_conditions(filters):
    conditions = ["gl.is_cancelled = 0"]
    values = {}

    if filters.get("company"):
        conditions.append("gl.company = %(company)s")
        values["company"] = filters.company
    if filters.get("ledger_account"):
        conditions.append("gl.account = %(ledger_account)s")
        values["ledger_account"] = filters.ledger_account
    if filters.get("party_type"):
        conditions.append("gl.party_type = %(party_type)s")
        values["party_type"] = filters.party_type
    if filters.get("party"):
        conditions.append("gl.party = %(party)s")
        values["party"] = filters.party

    return " AND ".join(conditions), values


def get_month_start(date_value):
    date_value = getdate(date_value)
    return date_value.replace(day=1)


def get_months(from_date, to_date):
    months = []
    current = get_month_start(from_date)
    end = get_month_start(to_date)
    while current <= end:
        months.append(current)
        current = add_months(current, 1)
    return months


def get_key(row):
    return (row.account or "", row.party_type or "", row.party or "")
