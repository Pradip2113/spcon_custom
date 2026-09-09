// Copyright (c) 2026, Sanpra and contributors
// For license information, please see license.txt

// frappe.query_reports["Lead Active-Inactive"] = {
// 	 filters: [
//         {
//             fieldname: "user",
//             label: __("User"),
//             fieldtype: "Link",
//             options: "User"
//         }
//     ]
// };



frappe.query_reports["Lead Active-Inactive"] = {
	filters: [{ fieldname: "report_type", label: __("Report Type"), fieldtype: "Select", options: ["Active / Non Active Wise", "Activities Wise"], default: "Active / Non Active Wise", reqd: 1 }, { fieldname: "user", label: __("User"), fieldtype: "Link", options: "User" }]
};
