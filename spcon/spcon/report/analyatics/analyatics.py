# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "name",
            "label": _("Lead ID"),
            "fieldtype": "Link",
            "options": "Lead",
            "width": 100
        },
        {
            "fieldname": "custom_lead_type",
            "label": _("Lead Type"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "creation",
            "label": _("Start Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "custom_closing_date",
            "label": _("Project Closing Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "source",
            "label": _("Source"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "custom_firm_name_lead",
            "label": _("Firm Name"),
            "fieldtype": "Link",
            "options": "Firm Name SPC",
            "width": 100
        },
        {
            "fieldname": "first_name",
            "label": _("Owner Name"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "custom_designation",
            "label": _("Designation"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "email_id",
            "label": _("Email"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "mobile_no",
            "label": _("Mobile No"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "custom_project",
            "label": _("Project Name"),
            "fieldtype": "Link",
            "options": "Project",
            "width": 100
        },
        {
            "fieldname": "custom_project_type",
            "label": _("Project Type"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "custom_project_address",
            "label": _("Project Address"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "custom_architecture",
            "label": _("Architect"),
            "fieldtype": "Link",
            "options": "Firm Name SPC",
            "width": 100
        },
        {
            "fieldname": "custom_consultant",
            "label": _("Consultant"),
            "fieldtype": "Link",
            "options": "Firm Name SPC",
            "width": 100
        },
        {
            "fieldname": "custom_contractor",
            "label": _("Contractor"),
            "fieldtype": "Link",
            "options": "Firm Name SPC",
            "width": 100
        },
        {
            "fieldname": "custom_applicator",
            "label": _("Applicator"),
            "fieldtype": "Link",
            "options": "Firm Name SPC",
            "width": 100
        },
        {
            "fieldname": "custom_other",
            "label": _("Other"),
            "fieldtype": "Link",
            "options": "Firm Name SPC",
            "width": 100
        },
        {
            "fieldname": "item_code",
            "label": _("Product Name"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 100
        },
        {
            "fieldname": "total_qty",
            "label": _("Qty"),
            "fieldtype": "Float",
            "width": 100
        }
    ]


def get_data(filters):
    data = []

    filters = filters or {}

    lead_filters = {}

    if filters.get("lead"):
        lead_filters["name"] = filters.get("lead")

    if filters.get("custom_lead_type"):
        lead_filters["custom_lead_type"] = filters.get("custom_lead_type")

    if filters.get("status"):
        lead_filters["status"] = filters.get("status")

    if filters.get("custom_firm_name_lead"):
        lead_filters["custom_firm_name_lead"] = filters.get("custom_firm_name_lead")

    if filters.get("custom_project"):
        lead_filters["custom_project"] = filters.get("custom_project")

    if filters.get("from_date") and filters.get("to_date"):
        lead_filters["creation"] = [
            "between",
            [filters.get("from_date"), filters.get("to_date")]
        ]
    elif filters.get("from_date"):
        lead_filters["creation"] = [">=", filters.get("from_date")]
    elif filters.get("to_date"):
        lead_filters["creation"] = ["<=", filters.get("to_date")]

    leads = frappe.get_all(
        "Lead",
        filters=lead_filters,
        fields=[
            "name",
            "custom_lead_type",
            "status",
            "creation",
            "custom_closing_date",
            "source",
            "custom_firm_name_lead",
            "first_name",
            "custom_designation",
            "email_id",
            "mobile_no",
            "custom_project",
            "custom_project_type",
            "custom_project_address",
            "custom_architecture",
            "custom_consultant",
            "custom_contractor",
            "custom_applicator",
            "custom_other",
        ],
        order_by="creation desc"
    )

    for lead in leads:
        doc = frappe.get_doc("Lead", lead.name)

        if doc.custom_project_items:
            for idx, item in enumerate(doc.custom_project_items):
                row = {}

                if idx == 0:
                    row.update({
                        "name": lead.name,
                        "custom_lead_type": lead.custom_lead_type,
                        "status": lead.status,
                        "creation": lead.creation,
                        "custom_closing_date": lead.custom_closing_date,
                        "source": lead.source,
                        "custom_firm_name_lead": lead.custom_firm_name_lead,
                        "first_name": lead.first_name,
                        "custom_designation": lead.custom_designation,
                        "email_id": lead.email_id,
                        "mobile_no": lead.mobile_no,
                        "custom_project": lead.custom_project,
                        "custom_project_type": lead.custom_project_type,
                        "custom_project_address": lead.custom_project_address,
                        "custom_architecture": lead.custom_architecture,
                        "custom_consultant": lead.custom_consultant,
                        "custom_contractor": lead.custom_contractor,
                        "custom_applicator": lead.custom_applicator,
                        "custom_other": lead.custom_other,
                    })
                else:
                    row.update({
                        "name": "",
                        "custom_lead_type": "",
                        "status": "",
                        "creation": "",
                        "custom_closing_date": "",
                        "source": "",
                        "custom_firm_name_lead": "",
                        "first_name": "",
                        "custom_designation": "",
                        "email_id": "",
                        "mobile_no": "",
                        "custom_project": "",
                        "custom_project_type": "",
                        "custom_project_address": "",
                        "custom_architecture": "",
                        "custom_consultant": "",
                        "custom_contractor": "",
                        "custom_applicator": "",
                        "custom_other": "",
                    })

                row["item_code"] = item.item_code
                row["total_qty"] = item.total_qty

                data.append(row)

        else:
            data.append({
                "name": lead.name,
                "custom_lead_type": lead.custom_lead_type,
                "status": lead.status,
                "creation": lead.creation,
                "custom_closing_date": lead.custom_closing_date,
                "source": lead.source,
                "custom_firm_name_lead": lead.custom_firm_name_lead,
                "first_name": lead.first_name,
                "custom_designation": lead.custom_designation,
                "email_id": lead.email_id,
                "mobile_no": lead.mobile_no,
                "custom_project": lead.custom_project,
                "custom_project_type": lead.custom_project_type,
                "custom_project_address": lead.custom_project_address,
                "custom_architecture": lead.custom_architecture,
                "custom_consultant": lead.custom_consultant,
                "custom_contractor": lead.custom_contractor,
                "custom_applicator": lead.custom_applicator,
                "custom_other": lead.custom_other,
                "item_code": "",
                "total_qty": 0,
            })

    return data