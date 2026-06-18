// // Copyright (c) 2026, Sanpra and contributors
// // For license information, please see license.txt

// frappe.query_reports["Task Department Wise Tracker"] = {
// 	"filters": [

// 	]
// };
 

frappe.query_reports["Task Department Wise Tracker"] = {
    filters: [
      {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end()
        },
        {
            fieldname: "summary_type",
            label: __("Summary Type"),
            fieldtype: "Select",
            options: "\nDepartment Wise\nEmployee Wise\nEmployee Department Wise",
            default: "Department Wise",
            reqd: 1
        }
    ]
};