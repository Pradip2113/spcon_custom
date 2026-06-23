import frappe


TASK_FIELDS = [
    "name",
    "subject",
    "status",
    "priority",
    "owner",
    "creation",
    "custom_posting_date",
    "exp_end_date",
    "custom_due_date_",
    "completed_on",
    "custom_last_discussion_",
    "custom_task_reporters",
]


@frappe.whitelist()
def get_task_dashboard(filters=None):
    filters = frappe.parse_json(filters) if filters else {}
    task_filters = build_task_filters(filters)

    tasks = frappe.get_all(
        "Task",
        filters=task_filters,
        fields=TASK_FIELDS,
        order_by="custom_due_date_ asc, creation desc",
    )

    result = []
    for task in tasks:
        departments = frappe.get_all(
            "Select Multi Department",
            filters={"parent": task.name, "parenttype": "Task"},
            pluck="department",
        )
        assign_to = frappe.get_all(
            "Task Multi Select Table",
            filters={"parent": task.name, "parenttype": "Task"},
            pluck="user",
        )

        task["departments"] = departments
        task["assign_to"] = assign_to
        task["assigned_date"] = task.get("custom_posting_date") or task.get("creation")
        task["effective_status"] = get_effective_status(task)
        result.append(task)

    result = apply_child_table_filters(result, filters)

    return {
        "tasks": result,
        "summary": get_summary(result),
        "filters": get_filter_options(),
    }


def build_task_filters(filters):
    task_filters = []

    if filters.get("from_date"):
        task_filters.append(["custom_posting_date", ">=", filters.get("from_date")])

    if filters.get("to_date"):
        task_filters.append(["custom_posting_date", "<=", filters.get("to_date")])

    if filters.get("search"):
        task_filters.append(["subject", "like", f"%{filters.get('search')}%"])

    return task_filters


def apply_child_table_filters(tasks, filters):
    department = filters.get("department")
    employee = filters.get("employee")
    status = filters.get("status")

    filtered = []
    for task in tasks:
        if department and department != "all" and department not in task.get("departments", []):
            continue

        if employee and employee != "all":
            people = set(task.get("assign_to", []))
            people.add(task.get("owner"))
            if task.get("custom_task_reporters"):
                people.add(task.get("custom_task_reporters"))
            if employee not in people:
                continue

        if status and status != "all" and task.get("effective_status") != status:
            continue

        filtered.append(task)

    return filtered


def get_effective_status(task):
    status = task.get("status") or "Open"
    if status in ["Open", "Working", "Completed", "Assigned"]:
        return status
    return status


def get_summary(tasks):
    counts = {"Open": 0, "Working": 0, "Completed": 0, "Assigned": 0}

    for task in tasks:
        status = task.get("effective_status") or get_effective_status(task)
        if status in counts:
            counts[status] += 1

    return {
        "total": len(tasks),
        "open": counts["Open"],
        "working": counts["Working"],
        "completed": counts["Completed"],
        "assigned": counts["Assigned"],
    }


def get_filter_options():
    departments = frappe.get_all(
        "Department",
        pluck="name",
        order_by="name asc",
    )
    employees = frappe.get_all(
        "Task Multi Select Table",
        filters={"parenttype": "Task"},
        pluck="user",
        distinct=True,
        order_by="user asc",
    )

    reporters = frappe.get_all(
        "Task",
        filters={"custom_task_reporters": ["is", "set"]},
        pluck="custom_task_reporters",
        distinct=True,
    )

    owners = frappe.get_all("Task", pluck="owner", distinct=True)

    return {
        "departments": sorted(set(filter(None, departments))),
        "employees": sorted(set(filter(None, employees + reporters + owners))),
    }
