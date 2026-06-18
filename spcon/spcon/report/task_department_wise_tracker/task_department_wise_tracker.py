import frappe


def execute(filters=None):
    filters = filters or {}

    summary_type = filters.get("summary_type")

    if summary_type == "Employee Wise":
        columns = get_employee_columns()
        data = get_employee_data(filters)

    elif summary_type == "Employee Department Wise":
        columns = get_employee_department_columns()
        data = get_employee_department_data(filters)

    else:
        columns = get_department_columns()
        data = get_department_data(filters)

    return columns, data


# =====================================================
# Department Wise Summary
# =====================================================

def get_department_columns():
    return [
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 220,
        },
        {
            "label": "Assigned",
            "fieldname": "assigned_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Open",
            "fieldname": "open_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Working",
            "fieldname": "working_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Completed",
            "fieldname": "completed_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Overdue",
            "fieldname": "overdue_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Total",
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 100,
        },
    ]


def get_department_data(filters):

    return frappe.db.sql(
        """
        SELECT

            IFNULL(emp.department, 'Not Assigned') AS department,

            SUM(
                CASE
                    WHEN t.status = 'Assigned'
                    THEN 1 ELSE 0
                END
            ) AS assigned_count,

            SUM(
                CASE
                    WHEN t.status = 'Open'
                    THEN 1 ELSE 0
                END
            ) AS open_count,

            SUM(
                CASE
                    WHEN t.status = 'Working'
                    THEN 1 ELSE 0
                END
            ) AS working_count,

            SUM(
                CASE
                    WHEN t.status = 'Completed'
                    THEN 1 ELSE 0
                END
            ) AS completed_count,

            SUM(
                CASE
                    WHEN t.status != 'Completed'
                    AND t.custom_due_date_ < CURDATE()
                    THEN 1 ELSE 0
                END
            ) AS overdue_count,

            COUNT(DISTINCT t.name) AS total

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

        GROUP BY emp.department

        ORDER BY emp.department
        """,
        filters,
        as_dict=1,
    )


# =====================================================
# Employee Wise Summary
# =====================================================

def get_employee_columns():
    return [
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Assigned",
            "fieldname": "assigned_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Open",
            "fieldname": "open_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Working",
            "fieldname": "working_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Completed",
            "fieldname": "completed_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Overdue",
            "fieldname": "overdue_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Total",
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 100,
        },
    ]


def get_employee_data(filters):

    return frappe.db.sql(
        """
        SELECT

            COALESCE(u.full_name, td.allocated_to) AS employee,

            SUM(
                CASE
                    WHEN t.status = 'Assigned'
                    THEN 1 ELSE 0
                END
            ) AS assigned_count,

            SUM(
                CASE
                    WHEN t.status = 'Open'
                    THEN 1 ELSE 0
                END
            ) AS open_count,

            SUM(
                CASE
                    WHEN t.status = 'Working'
                    THEN 1 ELSE 0
                END
            ) AS working_count,

            SUM(
                CASE
                    WHEN t.status = 'Completed'
                    THEN 1 ELSE 0
                END
            ) AS completed_count,

            SUM(
                CASE
                    WHEN t.status != 'Completed'
                    AND t.custom_due_date_ < CURDATE()
                    THEN 1 ELSE 0
                END
            ) AS overdue_count,

            COUNT(DISTINCT t.name) AS total

        FROM `tabTask` t

        LEFT JOIN `tabToDo` td
            ON td.reference_name = t.name
            AND td.reference_type = 'Task'
            AND td.status != 'Cancelled'

        LEFT JOIN `tabUser` u
            ON u.name = td.allocated_to

        WHERE DATE(t.creation)
            BETWEEN %(from_date)s
            AND %(to_date)s

        GROUP BY td.allocated_to

        ORDER BY employee
        """,
        filters,
        as_dict=1,
    )


# =====================================================
# Employee Department Wise Summary
# =====================================================

def get_employee_department_columns():
    return [
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": "Assigned",
            "fieldname": "assigned_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Open",
            "fieldname": "open_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Working",
            "fieldname": "working_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Completed",
            "fieldname": "completed_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Overdue",
            "fieldname": "overdue_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "Total",
            "fieldname": "total",
            "fieldtype": "Int",
            "width": 100,
        },
    ]


def get_employee_department_data(filters):

    data = frappe.db.sql(
        """
        SELECT

            IFNULL(t.custom_select_department, 'Not Assigned') AS department,
            COALESCE(u.full_name, td.allocated_to) AS employee,

            SUM(
                CASE
                    WHEN t.status = 'Assigned'
                    THEN 1 ELSE 0
                END
            ) AS assigned_count,

            SUM(
                CASE
                    WHEN t.status = 'Open'
                    THEN 1 ELSE 0
                END
            ) AS open_count,

            SUM(
                CASE
                    WHEN t.status = 'Working'
                    THEN 1 ELSE 0
                END
            ) AS working_count,

            SUM(
                CASE
                    WHEN t.status = 'Completed'
                    THEN 1 ELSE 0
                END
            ) AS completed_count,

            SUM(
                CASE
                    WHEN t.status != 'Completed'
                    AND t.custom_due_date_ < CURDATE()
                    THEN 1 ELSE 0
                END
            ) AS overdue_count,

            COUNT(DISTINCT t.name) AS total

        FROM `tabTask` t

        LEFT JOIN `tabToDo` td
            ON td.reference_name = t.name
            AND td.reference_type = 'Task'
            AND td.status != 'Cancelled'

        LEFT JOIN `tabUser` u
            ON u.name = td.allocated_to

        WHERE DATE(t.creation)
            BETWEEN %(from_date)s
            AND %(to_date)s

        GROUP BY
            t.custom_select_department,
            td.allocated_to

        ORDER BY
            t.custom_select_department,
            employee
        """,
        filters,
        as_dict=1,
    )

    previous_department = None

    for row in data:
        if row.department == previous_department:
            row.department = ""
        else:
            previous_department = row.department

    return data