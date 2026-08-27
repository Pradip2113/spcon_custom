import frappe


def execute():
    add_index("ToDo", ["reference_type", "reference_name", "allocated_to", "status"], "spcon_hpm_todo_ref_user")
    add_index("Permission Hierarchy Level", ["parent", "level_name"], "spcon_hpm_level_parent_name")
    add_index("Permission DocType Permission", ["parent", "doctype_name", "enabled"], "spcon_hpm_doctype_parent_enabled")


def add_index(doctype, fields, index_name):
    if not frappe.db.table_exists(doctype):
        return
    existing = frappe.db.sql(
        """
        select 1
        from information_schema.statistics
        where table_schema = database()
          and table_name = %s
          and index_name = %s
        limit 1
        """,
        (f"tab{doctype}", index_name),
    )
    if existing:
        return
    frappe.db.add_index(doctype, fields, index_name)
