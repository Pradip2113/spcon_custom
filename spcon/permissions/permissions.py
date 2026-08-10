import frappe

def get_company_condition(user):
    # get company
    company = frappe.db.get_value(
        "DefaultValue",
        {"parent": user, "defkey": "Company"},
        "defvalue"
    )

    # get doctype
    doctype = frappe.local.form_dict.get("doctype")

    # ❌ stop if missing
    if not company or not doctype:
        return ""

    # ❌ VERY IMPORTANT: avoid system/internal calls
    if frappe.local.form_dict.get("cmd") != "frappe.desk.reportview.get":
        return ""

    try:
        meta = frappe.get_meta(doctype)
    except:
        return ""

    # ❌ skip if no company field
    if not meta.has_field("company"):
        return ""

    return "`tab" + doctype + "`.company = '" + company + "'"



## Only show Customer to Assign sales person to Sales Perosn

def get_sales_person(user):
    if not user:
        return None

    sales_person_meta = frappe.get_meta("Sales Person")

    for user_field in ("user", "user_id"):
        if sales_person_meta.has_field(user_field):
            sales_person = frappe.db.get_value("Sales Person", {user_field: user}, "name")
            if sales_person:
                return sales_person

    if sales_person_meta.has_field("employee"):
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if employee:
            sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
            if sales_person:
                return sales_person

    full_name = frappe.db.get_value("User", user, "full_name")
    for candidate in (full_name, user):
        if not candidate:
            continue
        if frappe.db.exists("Sales Person", candidate):
            return candidate
        if sales_person_meta.has_field("sales_person_name"):
            sales_person = frappe.db.get_value("Sales Person", {"sales_person_name": candidate}, "name")
            if sales_person:
                return sales_person

    return None


def get_roles(user):
    return frappe.get_roles(user)


def is_manager(user, roles=None):
    roles = roles or get_roles(user)
    return "System Manager" in roles or "Sales Manager" in roles


def should_apply_sales_person_restriction(user):
    roles = get_roles(user)
    return "CRM Sales Person" in roles and not is_manager(user, roles)


def get_sales_person_customer_condition(user=None, table_alias="Customer"):
    user = user or frappe.session.user

    if not should_apply_sales_person_restriction(user):
        return ""

    sales_person = get_sales_person(user)

    if not sales_person:
        return "1=0"

    return f"""
        `{table_alias}`.custom_sales_person = {frappe.db.escape(sales_person)}
    """


def get_sales_person_customer_names(user=None):
    user = user or frappe.session.user

    if not should_apply_sales_person_restriction(user):
        return None

    sales_person = get_sales_person(user)

    if not sales_person:
        return []

    return frappe.get_all(
        "Customer",
        filters={"custom_sales_person": sales_person},
        pluck="name",
    )


def customer_query(user):
    return get_sales_person_customer_condition(user, "tabCustomer")


def sales_order_query(user):
    if not should_apply_sales_person_restriction(user):
        return ""

    sales_person = get_sales_person(user)

    if not sales_person:
        return "1=0"

    return f"""
        `tabSales Order`.customer IN (
            SELECT name
            FROM `tabCustomer`
            WHERE custom_sales_person = {frappe.db.escape(sales_person)}
        )
    """


def sales_invoice_query(user):
    if not should_apply_sales_person_restriction(user):
        return ""

    sales_person = get_sales_person(user)

    if not sales_person:
        return "1=0"

    return f"""
        `tabSales Invoice`.customer IN (
            SELECT name
            FROM `tabCustomer`
            WHERE custom_sales_person = {frappe.db.escape(sales_person)}
        )
    """


def delivery_note_query(user):
    if not should_apply_sales_person_restriction(user):
        return ""

    sales_person = get_sales_person(user)

    if not sales_person:
        return "1=0"

    return f"""
        `tabDelivery Note`.customer IN (
            SELECT name
            FROM `tabCustomer`
            WHERE custom_sales_person = {frappe.db.escape(sales_person)}
        )
    """
