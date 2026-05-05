frappe.ui.form.on('Sales Invoice', {
	async cost_center(frm) {
		if (!frm.doc.cost_center) {
			frm.set_value('company_address', '');
			return;
		}

		const r = await frappe.db.get_value('Cost Center', frm.doc.cost_center, 'custom_address');
		const address = r.message?.custom_address || '';
		frm.set_value('company_address', address);
		console.log(address);
		apply_warehouse_filter(frm)
	},
	onload: function(frm) {
		apply_warehouse_filter(frm);
	}
});


function apply_warehouse_filter(frm) {
    if (!frm.doc.cost_center) return;

    frm.set_query("set_warehouse", function() {
        return {
            query: "spcon.public.py.warehouse.get_warehouses_for_cost_center",
            filters: { 
                cost_center: frm.doc.cost_center
            }
        };
    });
}
