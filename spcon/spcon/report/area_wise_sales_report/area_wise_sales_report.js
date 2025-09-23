// Copyright (c) 2025, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["Area Wise Sales Report"] = {
	"filters": [
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{  
			fieldname: "doc_type",
			label: __("Document Type"),
			fieldtype: "Select",
			options: "Sales Invoice",
			default: "Sales Invoice",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "brand",
			label: __("Brand"),
			fieldtype: "Link",
			options: "Brand",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},  
		{  
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
			on_change: function () {
				frappe.query_report.set_filter_value("district", ""); 
				frappe.query_report.refresh(); 
			},
		},
		{
			fieldname: "district",
			label: __("District"),
			fieldtype: "Link",
			options: "District",
			get_query: function () {
				let state = frappe.query_report.get_filter_value("territory");
				if (state) {
					return {
						filters: {
							"state": state   // assumes District doctype has "state" field
						}
					};
				}
			},
		},
		{
			fieldname: "show_return_entries",
			label: __("Show Return Entries"),
			fieldtype: "Check",
			default: 1,
		},

	]
};
  