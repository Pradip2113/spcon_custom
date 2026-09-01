// Copyright (c) 2026, Sanpra and contributors
// For license information, please see license.txt

frappe.query_reports["Month-Wise Sale"] = {
	onload: function(report) {
		set_group_filter_visibility(report);
	},
	filters: [
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
			reqd: 1,
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: "Customer Wise\nItem Wise",
			default: "Customer Wise",
			reqd: 1,
			on_change: function() {
				set_group_filter_visibility(frappe.query_report);
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "item",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "view_by",
			label: __("View By"),
			fieldtype: "Select",
			options: "Amount Wise\nQty Wise",
			default: "Amount Wise",
			reqd: 1,
		},
	]
};


function set_group_filter_visibility(report) {
	let group_by = report.get_filter_value("group_by") || "Customer Wise";
	let show_customer = group_by === "Customer Wise";

	report.toggle_filter_display("customer", !show_customer);
	report.toggle_filter_display("item", show_customer);

	if (show_customer) {
		report.set_filter_value("item", "");
	} else {
		report.set_filter_value("customer", "");
	}
}
