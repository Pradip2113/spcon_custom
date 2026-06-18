# import frappe
# from frappe.utils import getdate, nowdate, date_diff


# def execute(filters=None):

#     if filters.get("view_type") == "Department Wise":
#         columns = get_department_columns()
#         data = get_department_data(filters)
#     else:
#         columns = get_employee_columns()
#         data = get_employee_data(filters)

#     return columns, data


# # ==========================
# # Department Wise
# # ==========================

# def get_department_columns():
#     return [
#         {
#             "label": "Department",
#             "fieldname": "department",
#             "fieldtype": "Link",
#             "options": "Department",
#             "width": 200,
#         },
#         {
#             "label": "Open",
#             "fieldname": "open_count",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#         {
#             "label": "Working",
#             "fieldname": "working_count",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#         {
#             "label": "Completed",
#             "fieldname": "completed_count",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#         {
#             "label": "Cancelled",
#             "fieldname": "cancelled_count",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#         {
#             "label": "Overdue",
#             "fieldname": "overdue_count",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#         {
#             "label": "Total",
#             "fieldname": "total",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#     ]


# def get_department_data(filters):

#     return frappe.db.sql(
#         """
#         SELECT
#             IFNULL(emp.department, 'Not Assigned') AS department,

#             SUM(
#                 CASE
#                     WHEN t.status='Open'
#                     THEN 1 ELSE 0
#                 END
#             ) AS open_count,

#             SUM(
#                 CASE
#                     WHEN t.status IN ('Working','In Progress')
#                     THEN 1 ELSE 0
#                 END
#             ) AS working_count,

#             SUM(
#                 CASE
#                     WHEN t.status='Completed'
#                     THEN 1 ELSE 0
#                 END
#             ) AS completed_count,

#             SUM(
#                 CASE
#                     WHEN t.status='Cancelled'
#                     THEN 1 ELSE 0
#                 END
#             ) AS cancelled_count,

#             SUM(
#                 CASE
#                     WHEN t.status!='Completed'
#                     AND t.custom_due_date_ < CURDATE()
#                     THEN 1 ELSE 0
#                 END
#             ) AS overdue_count,

#             COUNT(DISTINCT t.name) AS total

#         FROM `tabTask` t

#         LEFT JOIN `tabToDo` td
#             ON td.reference_name = t.name
#             AND td.reference_type = 'Task'
#             AND td.status != 'Cancelled'

#         LEFT JOIN `tabEmployee` emp
#             ON emp.user_id = td.allocated_to

#         WHERE DATE(t.creation)
#         BETWEEN %(from_date)s AND %(to_date)s

#         GROUP BY emp.department
#         ORDER BY emp.department
#         """,
#         filters,
#         as_dict=1,
#     )


# # ==========================
# # Employee Wise
# # ==========================

# def get_employee_columns():
#     return [
#         {
#             "label": "Task ID",
#             "fieldname": "name",
#             "fieldtype": "Link",
#             "options": "Task",
#             "width": 180,
#         },
#         {
#             "label": "Subject",
#             "fieldname": "subject",
#             "fieldtype": "Data",
#             "width": 250,
#         },
#         {
#             "label": "Department",
#             "fieldname": "department",
#             "fieldtype": "Link",
#             "options": "Department",
#             "width": 150,
#         },
#         {
#             "label": "Status",
#             "fieldname": "status",
#             "fieldtype": "Data",
#             "width": 120,
#         },
#         {
#             "label": "Priority",
#             "fieldname": "priority",
#             "fieldtype": "Data",
#             "width": 100,
#         },
#         {
#             "label": "Assigned By",
#             "fieldname": "assigned_by",
#             "fieldtype": "Data",
#             "width": 180,
#         },
#         {
#             "label": "Assigned To",
#             "fieldname": "assigned_to",
#             "fieldtype": "Data",
#             "width": 180,
#         },
#         {
#             "label": "Posting Date",
#             "fieldname": "posting_date",
#             "fieldtype": "Date",
#             "width": 120,
#         },
#         {
#             "label": "Due Date",
#             "fieldname": "due_date",
#             "fieldtype": "Date",
#             "width": 120,
#         },
#         {
#             "label": "Completion Date",
#             "fieldname": "completion_date",
#             "fieldtype": "Date",
#             "width": 120,
#         },
#         {
#             "label": "Delay Days",
#             "fieldname": "delay_days",
#             "fieldtype": "Int",
#             "width": 100,
#         },
#     ]


# def get_employee_data(filters):

#     conditions = ""

#     if filters.get("assigned_by"):
#         conditions += " AND t.owner = %(assigned_by)s"

#     if filters.get("assigned_to"):
#         conditions += " AND td.allocated_to = %(assigned_to)s"

#     data = frappe.db.sql(
#         f"""
#         SELECT
#             t.name,
#             t.subject,
#             t.status,
#             t.priority,
#             t.owner,
#             DATE(t.creation) AS posting_date,
#             t.custom_due_date_ AS due_date,
#             t.completed_on AS completion_date,
#             td.allocated_to,
#             emp.department

#         FROM `tabTask` t

#         LEFT JOIN `tabToDo` td
#             ON td.reference_name = t.name
#             AND td.reference_type = 'Task'
#             AND td.status != 'Cancelled'

#         LEFT JOIN `tabEmployee` emp
#             ON emp.user_id = td.allocated_to

#         WHERE DATE(t.creation)
#         BETWEEN %(from_date)s
#         AND %(to_date)s

#         {conditions}

#         ORDER BY t.creation DESC
#         """,
#         filters,
#         as_dict=1,
#     )

#     today = getdate(nowdate())

#     for row in data:

#         row.assigned_by = (
#             frappe.db.get_value(
#                 "User",
#                 row.owner,
#                 "full_name"
#             ) or row.owner
#         )

#         row.assigned_to = (
#             frappe.db.get_value(
#                 "User",
#                 row.allocated_to,
#                 "full_name"
#             )
#             if row.allocated_to else ""
#         )

#         row.delay_days = 0

#         if row.due_date:

#             due_date = getdate(row.due_date)

#             if row.status == "Completed" and row.completion_date:

#                 completion_date = getdate(
#                     row.completion_date
#                 )

#                 if completion_date > due_date:

#                     row.delay_days = date_diff(
#                         completion_date,
#                         due_date
#                     )

#             elif today > due_date:

#                 row.delay_days = date_diff(
#                     today,
#                     due_date
#                 )

#     return data

import frappe
from frappe.utils import getdate, nowdate, date_diff


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Task ID",
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Task",
            "width": 180,
        },
        {
            "label": "Subject",
            "fieldname": "subject",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 150,
        },
        {
            "label": "Status",
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": "Priority",
            "fieldname": "priority",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Assigned By",
            "fieldname": "assigned_by",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Assigned To",
            "fieldname": "assigned_to",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Posting Date",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": "Due Date",
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": "Completion Date",
            "fieldname": "completion_date",
            "fieldtype": "Date",
            "width": 130,
        },
        {
            "label": "Delay Days",
            "fieldname": "delay_days",
            "fieldtype": "Int",
            "width": 100,
        },
    ]


def get_data(filters):

    conditions = ""

    if filters.get("assigned_by"):
        conditions += " AND t.owner = %(assigned_by)s"

    if filters.get("assigned_to"):
        conditions += " AND td.allocated_to = %(assigned_to)s"

    data = frappe.db.sql(
        f"""
        SELECT
            t.name,
            t.subject,
            t.status,
            t.priority,
            t.owner,
            DATE(t.creation) AS posting_date,
            t.custom_due_date_ AS due_date,
            t.completed_on AS completion_date,
            td.allocated_to,
            emp.department

        FROM `tabTask` t

        LEFT JOIN `tabToDo` td
            ON td.reference_name = t.name
            AND td.reference_type = 'Task'
            AND td.status != 'Cancelled'

        LEFT JOIN `tabEmployee` emp
            ON emp.user_id = td.allocated_to

        WHERE DATE(t.creation)
            BETWEEN %(from_date)s
            AND %(to_date)s

        {conditions}

        ORDER BY t.creation DESC
        """,
        filters,
        as_dict=1,
    )

    today = getdate(nowdate())

    for row in data:

        row.assigned_by = (
            frappe.db.get_value(
                "User",
                row.owner,
                "full_name"
            ) or row.owner
        )

        row.assigned_to = (
            frappe.db.get_value(
                "User",
                row.allocated_to,
                "full_name"
            )
            if row.allocated_to else ""
        )

        row.delay_days = 0

        if row.due_date:

            due_date = getdate(row.due_date)

            if row.status == "Completed" and row.completion_date:

                completion_date = getdate(row.completion_date)

                if completion_date > due_date:
                    row.delay_days = date_diff(
                        completion_date,
                        due_date
                    )

            elif today > due_date:

                row.delay_days = date_diff(
                    today,
                    due_date
                )

    return data