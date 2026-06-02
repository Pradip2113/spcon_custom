frappe.ui.form.on('Purchase Order', {
	async cost_center(frm) {
		if (!frm.doc.cost_center) {
			frm.set_value('billing_address', '');
			return;
		}
 
		const r = await frappe.db.get_value('Cost Center', frm.doc.cost_center, 'custom_address');
		const address = r.message?.custom_address || '';
		frm.set_value('billing_address', address);
		console.log(address);
		apply_warehouse_filter(frm);
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
(function () {
    function use_spcon_inter_company_mapper() {
        if (!window.erpnext || !erpnext.buying || !erpnext.buying.PurchaseOrderController) {
            return;
        }

        if (erpnext.buying.PurchaseOrderController.prototype._spcon_inter_company_mapper) {
            return;
        }

        erpnext.buying.PurchaseOrderController.prototype.make_inter_company_order = function(frm) {
            frappe.model.open_mapped_doc({
                method: "spcon.public.py.inter_company_order.make_inter_company_sales_order",
                frm: frm,
            });
        };
        erpnext.buying.PurchaseOrderController.prototype._spcon_inter_company_mapper = true;
    }

    frappe.ui.form.on("Purchase Order", {
        setup() {
            use_spcon_inter_company_mapper();
        },
        refresh() {
            use_spcon_inter_company_mapper();
        },
    });
})();
