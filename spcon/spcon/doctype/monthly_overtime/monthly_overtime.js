// Copyright (c) 2024, Sanpra and contributors
// For license information, please see license.txt

frappe.ui.form.on("Monthly Overtime", {
    start_date: function(frm) {
        if (frm.doc.start_date) {
            const startDate = frappe.datetime.str_to_obj(frm.doc.start_date); // Convert string to Date object
            const year = startDate.getFullYear();
            const month = startDate.getMonth(); // Months are zero-based (0 = January)
            // Get the last day of the month
            const lastDay = new Date(year, month + 1, 0).getDate(); // Moving to the next month, day 0 gives the last day of the current month
            // Set the end_date
            const endDate = new Date(year, month, lastDay); // Construct the end_date
            frm.set_value('end_date', frappe.datetime.obj_to_str(endDate)); // Convert Date object to string and set it
        }
    },
    get_details: function (frm) {
		frm.clear_table("item_ot")
		frm.refresh_field('item_ot')		
		frm.call({
			method:'getitems',
			doc: frm.doc
		});
	}
});

	
