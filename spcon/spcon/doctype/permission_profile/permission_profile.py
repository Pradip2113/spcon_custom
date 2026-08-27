import frappe
from frappe.model.document import Document

from spcon.hierarchical_permissions.manager import apply_profile, clear_permission_profile_cache, validate_profile


class PermissionProfile(Document):
    def validate(self):
        validate_profile(self)

    def on_update(self):
        apply_profile(self)

    def on_submit(self):
        apply_profile(self)

    def on_cancel(self):
        clear_permission_profile_cache()
        frappe.clear_cache()
