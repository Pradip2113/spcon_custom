// // Copyright (c) 2026, Sanpra and contributors
// // For license information, please see license.txt

// frappe.query_reports["Task Tracker"] = {
// 	"filters": [

// 	]
// };
 

frappe.query_reports["Task Tracker"] = {
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
            fieldname: "assigned_by",
            label: __("Assigned By"),
            fieldtype: "Link",
            options: "User"
        },
        {
            fieldname: "assigned_to",
            label: __("Assigned To"),
            fieldtype: "Link",
            options: "User"
        }
    ]
};