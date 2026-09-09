# import frappe
# from frappe import _


# def execute(filters=None):
#     filters = filters or {}

#     columns = get_columns()
#     data = get_data(filters)

#     return columns, data


# def get_columns():
#     return [
#         {
#             "label": _("User"),
#             "fieldname": "user",
#             "fieldtype": "Link",
#             "options": "User",
#             "width": 220,
#         },
#         {
#             "label": _("Total Lead"),
#             "fieldname": "total_lead",
#             "fieldtype": "Int",
#             "width": 120,
#         },
#         {
#             "label": _("Active Lead"),
#             "fieldname": "active_lead",
#             "fieldtype": "Int",
#             "width": 120,
#         },
#         {
#             "label": _("Non-Active Lead"),
#             "fieldname": "non_active_lead",
#             "fieldtype": "Int",
#             "width": 150,
#         },
#     ]


# def get_data(filters):
#     conditions = []
#     values = {}

#     # User filter
#     if filters.get("user"):
#         conditions.append("l.owner = %(user)s")
#         values["user"] = filters.get("user")

#     where_condition = ""

#     if conditions:
#         where_condition = "WHERE " + " AND ".join(conditions)

#     leads = frappe.db.sql(
#         f"""
#         SELECT
#             l.name,
#             l.owner AS user,
#             l.modified,

#             (
#                 SELECT MAX(e.creation)
#                 FROM `tabEvent` e
#                 WHERE
#                     e.reference_doctype = 'Lead'
#                     AND e.reference_docname = l.name
#             ) AS last_event

#         FROM `tabLead` l

#         {where_condition}

#         ORDER BY l.owner
#         """,
#         values,
#         as_dict=True,
#     )

#     result = {}

#     cutoff_date = frappe.utils.add_days(
#         frappe.utils.now_datetime(),
#         -15
#     )

#     for lead in leads:

#         user = lead.user

#         if user not in result:
#             result[user] = {
#                 "user": user,
#                 "total_lead": 0,
#                 "active_lead": 0,
#                 "non_active_lead": 0,
#             }

#         result[user]["total_lead"] += 1

#         # Latest activity between Lead modification and Event
#         last_activity = lead.modified

#         if lead.last_event and lead.last_event > last_activity:
#             last_activity = lead.last_event

#         # Active if activity is within 15 days
#         if last_activity >= cutoff_date:
#             result[user]["active_lead"] += 1
#         else:
#             result[user]["non_active_lead"] += 1

#     return list(result.values())






import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}

    report_type = filters.get("report_type") or "Active / Non Active Wise"

    if report_type == "Activities Wise":
        columns = get_activity_columns()
        data = get_activity_data(filters)
    else:
        columns = get_summary_columns()
        data = get_summary_data(filters)

    return columns, data


# =========================================================
# ACTIVE / NON ACTIVE WISE
# =========================================================

def get_summary_columns():
    return [
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Link",
            "options": "User",
            "width": 250,
        },
        {
            "label": _("Total Lead"),
            "fieldname": "total_lead",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Active Lead"),
            "fieldname": "active_lead",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": _("Non-Active Lead"),
            "fieldname": "non_active_lead",
            "fieldtype": "Int",
            "width": 150,
        },
    ]


def get_summary_data(filters):
    conditions = []
    values = {}

    # User filter
    if filters.get("user"):
        conditions.append("l.owner = %(user)s")
        values["user"] = filters.get("user")

    where_condition = ""

    if conditions:
        where_condition = "WHERE " + " AND ".join(conditions)

    leads = frappe.db.sql(
        f"""
        SELECT
            l.name,
            l.owner AS user,
            l.modified,

            (
                SELECT MAX(e.creation)
                FROM `tabEvent` e
                WHERE
                    e.reference_doctype = 'Lead'
                    AND e.reference_docname = l.name
            ) AS last_event

        FROM `tabLead` l

        {where_condition}

        ORDER BY
            l.owner,
            l.name
        """,
        values,
        as_dict=True,
    )

    result = {}

    # 15 days cutoff
    cutoff_date = frappe.utils.add_days(
        frappe.utils.now_datetime(),
        -15
    )

    for lead in leads:

        user = lead.user

        if user not in result:
            result[user] = {
                "user": user,
                "total_lead": 0,
                "active_lead": 0,
                "non_active_lead": 0,
            }

        # Total Lead
        result[user]["total_lead"] += 1

        # -------------------------------------------------
        # Find latest activity
        # -------------------------------------------------

        last_activity = lead.modified

        if lead.last_event and lead.last_event > last_activity:
            last_activity = lead.last_event

        # -------------------------------------------------
        # Active / Non Active
        # -------------------------------------------------

        if last_activity >= cutoff_date:
            result[user]["active_lead"] += 1
        else:
            result[user]["non_active_lead"] += 1

    return list(result.values())


# =========================================================
# ACTIVITIES WISE
# =========================================================

def get_activity_columns():
    return [
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Link",
            "options": "User",
            "width": 250,
        },
        {
            "label": _("Lead"),
            "fieldname": "lead",
            "fieldtype": "Link",
            "options": "Lead",
            "width": 180,
        },
        {
            "label": _("Lead Creation Date"),
            "fieldname": "lead_creation_date",
            "fieldtype": "Date",
            "width": 160,
        },
        {
            "label": _("Activity"),
            "fieldname": "activity",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": _("Follow-up Date"),
            "fieldname": "followup_date",
            "fieldtype": "Date",
            "width": 180,
        },
        {
            "label": _("Follow-up Status"),
            "fieldname": "followup_status",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


def get_activity_data(filters):

    conditions = [
        "e.reference_doctype = 'Lead'",
        "e.reference_docname IS NOT NULL",
    ]

    values = {}

    # User filter
    if filters.get("user"):
        conditions.append("l.owner = %(user)s")
        values["user"] = filters.get("user")

    where_condition = " AND ".join(conditions)

    activities = frappe.db.sql(
        f"""
        SELECT
            l.owner AS user,
            l.name AS lead,
            DATE(l.creation) AS lead_creation_date,
            e.description AS activity,
            e.starts_on AS followup_date,
            e.status AS followup_status,
            e.creation AS event_creation

        FROM `tabLead` l

        INNER JOIN `tabEvent` e
            ON e.reference_doctype = 'Lead'
            AND e.reference_docname = l.name

        WHERE
            {where_condition}

        ORDER BY
            l.owner,
            l.name,
            e.creation DESC
        """,
        values,
        as_dict=True,
    )

    # -----------------------------------------------------
    # Show User and Lead only once for multiple Events
    # -----------------------------------------------------

    previous_user = None
    previous_lead = None

    for row in activities:

        current_user = row.user
        current_lead = row.lead

        # If same User + Lead as previous row,
        # hide User and Lead
        if (
            current_user == previous_user
            and current_lead == previous_lead
        ):
            row.user = ""
            row.lead = ""
            row.lead_creation_date = ""

        previous_user = current_user
        previous_lead = current_lead

        # Remove internal field
        row.pop("event_creation", None)

    return activities
