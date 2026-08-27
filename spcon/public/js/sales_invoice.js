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
	onload(frm) {
		apply_warehouse_filter(frm);
	},
	refresh(frm) {
		setTimeout(() => set_sales_order_remark(frm), 300);
	},
	get_items(frm) {
		setTimeout(() => set_sales_order_remark(frm), 500);
	},
	async validate(frm) {
		await set_sales_order_remark(frm);
	}
});

frappe.ui.form.on('Sales Invoice Item', {
	items_add(frm) {
		set_sales_order_remark(frm);
	},
	items_remove(frm) {
		set_sales_order_remark(frm);
	},
	sales_order(frm) {
		set_sales_order_remark(frm);
	},
	item_code(frm) {
		setTimeout(() => set_sales_order_remark(frm), 300);
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

function set_sales_order_remark(frm) {
	const sales_orders = [
		...new Set((frm.doc.items || []).map((row) => row.sales_order).filter(Boolean))
	];

	if (!sales_orders.length) {
		return frm.set_value('custom_remark', '');
	}

	return frappe.call({
		method: 'spcon.public.py.sales_invoice.get_sales_order_remark',
		args: { sales_orders },
		callback(r) {
			frm.set_value('custom_remark', r.message || '');
		}
	});
}
