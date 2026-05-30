app_name = "spcon"
app_title = "spcon"
app_publisher = "Sanpra"
app_description = "spcon"
app_email = "21pradipjadhav@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "spcon",
# 		"logo": "/assets/spcon/logo.png",
# 		"title": "spcon",
# 		"route": "/spcon",
# 		"has_permission": "spcon.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/spcon/css/spcon.css"
# app_include_js = "/assets/spcon/js/spcon.js"
app_include_js = [
    "/assets/spcon/js/hide_item_name.js",
    "/assets/spcon/js/hide_item_name_doctype.js",
    "/assets/spcon/js/custom_navbar.js"
] 

# include js, css files in header of web template
# web_include_css = "/assets/spcon/css/spcon.css" 
# web_include_js = "/assets/spcon/js/spcon.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "spcon/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"Employee Checkin" : "public/js/custom_employee_checkin.js"}
# doctype_js = {"Stock Entry" : "public/js/custom_stock_entry.js"}
# doctype_js = {"Work Order" : "public/js/custom_work_order.js"}
# doctype_js = {"Employee Advance" : "public/js/custom_employee_advance.js"}
# doctype_js = {"Customer": "public/js/customer.js"}
# doctype_js = {"Lead": "public/js/lead.js"}
# doctype_js = {"Sales Order": "public/js/sales_order.js"}

doctype_js = {
    "Employee Checkin" : "public/js/custom_employee_checkin.js",
    "Stock Entry" : "public/js/custom_stock_entry.js",
    "Work Order" : "public/js/custom_work_order.js",
    "Employee Advance" : "public/js/custom_employee_advance.js",
    "Customer": "public/js/customer.js",
    "Lead": "public/js/lead.js",
    "Attendance Request": "public/js/attendance_request.js",
    "BOM": "public/js/bom.js",
    "Quotation": "public/js/quotation.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Sales Order": "public/js/sales_order.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Cost Center": "public/js/cost_center.js",
    "Material Request": "public/js/material_request.js",
}

doctype_list_js = {
    "BOM": "public/js/bom_list.js",
    "Purchase Order": "public/listview/purchase_order_list.js",
}
 
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "spcon/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "spcon.utils.jinja_methods",
# 	"filters": "spcon.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "spcon.install.before_install"
# after_install = "spcon.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "spcon.uninstall.before_uninstall"
# after_uninstall = "spcon.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "spcon.utils.before_app_install"
# after_app_install = "spcon.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "spcon.utils.before_app_uninstall"
# after_app_uninstall = "spcon.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "spcon.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
#     "Lead": "spcon.public.py.permissions.get_permission_query_conditions",
# }
permission_query_conditions = {
    "*": "spcon.permissions.permissions.get_company_condition"
}



# has_permission = {
#     "Lead": "spcon.public.py.permissions.has_permission"
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Customer": "spcon.override.customer.CustomCustomer",
    "Supplier": "spcon.override.supplier.CustomSupplier",
	"Salary Slip": "spcon.override.salary_slip.CustomSalarySlip",
    "Employee Advance": "spcon.override.employee_advance.CustomEmployeeAdvance",
    "Additional Salary": "spcon.override.additional_salary.CustomAdditionalSalary",
    "Lead": "spcon.public.py.lead.CustomLead"
}

 
# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
    "Employee Checkin":{
        "before_save":"spcon.override.employee_checkin.geo_fencing"
    },
    "Attendance":{
        # "on_submit":"spcon.hrms_case.sandwich.apply_sandwich_rule_on_attendance_save",
        "on_submit":"spcon.hrms_case.sandwich.apply_sandwich_rule_on_attendance_save",
        "before_submit":"spcon.public.py.attendance.mark_attendance",
    },
    "Shift Type":{
        "before_save":"spcon.hrms_case.shift_type.work_hrs_cal"
    },
    "Salary Slip":{
        "before_insert":"spcon.override.salary_slip.hrs_ot"
    },
     "Work Order":{
        "after_save":"spcon.manufacuring.custom_work_order.bom_set_name"
    },
    "Material Request": {
        "before_cancel": "spcon.public.py.material_request.get_data",
        "validate": "spcon.public.py.set_cost_center.set_material_request_cost_center"
    },
    "Leave Application": {
        "on_submit": "spcon.public.py.leave_application.set_leave_type_absent"
    },
    "Expense Claim": {
        "on_submit": "spcon.public.py.employee_advance.get_outstanding"
    },
    "Attendance Request": {
        "before_save": [
            "spcon.public.py.attendance_request.purpose_limit",
            "spcon.public.py.attendance_request.validate_late_entry_attendance",   
            "spcon.public.py.attendance_request.made_attachment_required"
        ] 
        # "on_submit": [
        #     "spcon.public.py.attendance_request.validate_late_entry_attendance",
        #     "spcon.public.py.attendance_request.made_attachment_required"
        # ] 
    },
    "Quality Inspection": {
        "before_submit": "spcon.public.py.quality_inspection.set_parametor_mandetory"
    },
    "Lead": {
        "before_save": "spcon.public.py.lead.set_title_field",
    },
    "Purchase Order": {
        "before_save": [
            "spcon.public.py.purchase_order.set_po_pending_status",
            "spcon.public.py.set_cost_center.set_cost_center"
        ] 
    },
    "Purchase Receipt": {
        "before_save": [
            "spcon.public.py.purchase_receipt.validate_over_receipt_with_draft",
            "spcon.public.py.set_cost_center.set_cost_center"
        ] 
    },
    "Purchase Invoice": {
        "before_save" : [
            "spcon.public.py.set_cost_center.set_cost_center",
            "spcon.public.py.sales_invoice.validate_naming_series"
        ] 
    },
    "Sales Order": {
        "before_save": [
            "spcon.override.sales_order_dates.sync_draft_item_dates",
            "spcon.public.py.sales_order.set_minimum_qty",
            "spcon.public.py.set_cost_center.set_cost_center"
        ],
        "on_update_after_submit": "spcon.public.py.set_cost_center.on_update_set_cost_center"
    },
    "Sales Invoice": {
        "before_save": [
            "spcon.public.py.sales_invoice.set_actual_dispatch_date_on_save",
            "spcon.public.py.sales_invoice.set_minimum_qty",
            "spcon.public.py.set_cost_center.set_cost_center",
            "spcon.public.py.sales_invoice.validate_naming_series"
        ] 
    },
    "Delivery Note": {
        "before_save": [
            "spcon.public.py.sales_order.set_minimum_qty",
            "spcon.public.py.set_cost_center.set_cost_center"
        ]
    },
    "Payment Entry": {
        "before_save": "spcon.public.py.set_cost_center.set_cost_center_payment_entry"
    },
    "Journal Entry": {
        "before_save": "spcon.public.py.set_cost_center.set_cost_center_journal_entry"
    },
} 
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"spcon.tasks.all"
# 	],
# 	"daily": [
# 		"spcon.tasks.daily"
# 	],
# 	"hourly": [
# 		"spcon.tasks.hourly"
# 	],
# 	"weekly": [
# 		"spcon.tasks.weekly"
# 	],
# 	"monthly": [
# 		"spcon.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "spcon.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.controllers.accounts_controller.update_child_qty_rate":
        "spcon.override.sales_order_dates.update_child_qty_rate"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "spcon.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["spcon.utils.before_request"]
# after_request = ["spcon.utils.after_request"]

# Job Events
# ----------
# before_job = ["spcon.utils.before_job"]
# after_job = ["spcon.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"spcon.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
