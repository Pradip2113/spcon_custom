// Copyright (c) 2026, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["Analyatics"] = {
	filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date"
        },
        {
            fieldname: "lead",
            label: __("Lead ID"),
            fieldtype: "Link",
            options: "Lead"
        },
        {
            fieldname: "custom_lead_type",
            label: __("Lead Type"),
            fieldtype: "Data"
        },
        {
            fieldname: "status",
            label: __("Status"),
            fieldtype: "Select",
            options: [
                "",
                "Lead",
                "Open",
                "Replied",
                "Opportunity",
                "Quotation",
                "Lost Quotation",
                "Interested",
                "Converted",
                "Do Not Contact"
            ]
        },
        {
            fieldname: "custom_firm_name_lead",
            label: __("Firm Name"),
            fieldtype: "Link",
            options: "Firm Name SPC"
        },
        {
            fieldname: "custom_project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project"
        }
    ]
};