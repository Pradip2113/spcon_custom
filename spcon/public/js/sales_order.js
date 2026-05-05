// frappe.ui.form.on("Sales Order Item", {
// 	custom_check_rate(frm, cdt, cdn) {
// 		const row = locals[cdt][cdn];

// 		if (!frm.doc.customer) {
// 			frappe.msgprint(__("Please select a customer first."));
// 			return;
// 		}

// 		if (!row.item_code) {
// 			frappe.msgprint(__("Please select an item first."));
// 			return;
// 		}

// 		frappe.call({
// 			method: "spcon.public.py.sales_order.get_last_5_sale_rates",
// 			args: { 
// 				customer: frm.doc.customer,
// 				item_code: row.item_code,
// 			},
// 			freeze: true,
// 			callback: function (r) {
// 				const rates = r.message || [];
// 				show_rate_history_dialog(frm.doc.customer, row.item_code, rates);
// 			},
// 		});
// 	},
// });

// function show_rate_history_dialog(customer, item_code, rates) {
// 	const dialog = new frappe.ui.Dialog({
// 		title: __("Last 5 Invoice Rates"),
// 		fields: [
// 			{
// 				fieldtype: "HTML",
// 				fieldname: "rate_history_html",
// 			},
// 		],
// 		size: "large",
// 	});

// 	const html = rates.length
// 		? `
// 			<div class="table-responsive">
// 				<table class="table table-bordered table-striped">
// 					<thead>
// 						<tr>
// 							<th>${__("Item")}</th>
// 							<th>${__("Rate")}</th>
// 						</tr>
// 					</thead>
// 					<tbody> 
// 						${rates
// 							.map(
// 								(row) => `
// 									<tr>
// 										<td>${frappe.utils.escape_html(row.item_name || row.item_code || "")}</td>
// 										<td style="text-align: right;">${frappe.format(row.rate, { fieldtype: "Currency" }) || ""}</td>
// 									</tr>
// 								`
// 							)
// 							.join("")}
// 					</tbody>
// 				</table>
// 			</div>
// 		`
// 		: `
// 			<p>${__("No submitted sales invoice rates were found for this customer and item.")}</p>
// 		`;

// 	dialog.fields_dict.rate_history_html.$wrapper.html(html);
// 	dialog.show();
// }


frappe.ui.form.on('Sales Order', {
	async cost_center(frm) {
		if (!frm.doc.cost_center) {
			frm.set_value('company_address', '');
			return;
		}

		const r = await frappe.db.get_value('Cost Center', frm.doc.cost_center, 'custom_address');
		const address = r.message?.custom_address || '';
		frm.set_value('company_address', address);
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




frappe.ui.form.on('Sales Order Item', {
    custom_check_rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!frm.doc.customer || !row.item_code) {
            frappe.msgprint("Customer and Item required");
            return;
        }

        frappe.call({
            method: "spcon.public.py.sales_order.get_latest_rate",
            args: {
                customer: frm.doc.customer,
                item_code: row.item_code
            },
            callback: function(r) {
                if (r.message && r.message.length) {

                    let msg = "<b>Last 5 Rates:</b><br><br>";

                    r.message.forEach(d => {
                        msg += `Invoice: ${d.invoice} | Date: ${d.posting_date} | Rate: ${d.rate}<br>`;
                    });

                    frappe.msgprint(msg);

                } else {
                    frappe.msgprint("No previous Sales Invoice found");
                }
            }
        });
    }
});