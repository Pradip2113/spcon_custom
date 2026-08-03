# import frappe

# def get_permission_query_conditions(user):
#     """Return SQL condition to filter Lead list view."""
#     if not user:
#         user = frappe.session.user

#     if user == "Administrator" or "System Manager" in frappe.get_roles(user):
#         return ""

#     user_esc = f"'{frappe.db.escape(user)}'"

#     return f"""
#         (
#             `tabLead`.owner = {user_esc}
#             OR `tabLead`.name IN (
#                 SELECT reference_name FROM `tabToDo`
#                 WHERE reference_type='Lead' AND owner={user_esc}
#             )
#             OR `tabLead`.assigned_to LIKE '%{user}%'
#         )
#     """

# def has_permission(doc, user=None):
#     """Allow user to open only their assigned or owned leads."""
#     if not user:
#         user = frappe.session.user

#     if user == "Administrator" or "System Manager" in frappe.get_roles(user):
#         return True

#     # If user is creator
#     if doc.owner == user:
#         return True

#     # If using assigned_to custom field (comma-separated users)
#     if hasattr(doc, "assigned_to") and doc.assigned_to:
#         assigned_users = [u.strip() for u in doc.assigned_to.split(",")]
#         if user in assigned_users:
#             return True

#     # If assigned via ToDo
#     exists = frappe.db.exists("ToDo", {
#         "reference_type": "Lead",
#         "reference_name": doc.name,
#         "owner": user
#     })
#     if exists:
#         return True

#     return False


