frappe.listview_settings["BOM"] = {
    onload(listview) {
        listview.page.add_inner_button(__("RCM Calculate"), function() {
            const selected_boms = listview.get_checked_items().map((item) => item.name);

            if (!selected_boms.length) {
                frappe.msgprint(__("Please select at least one BOM."));
                return;
            }

            frappe.call({
                method: "spcon.public.py.bom.calculate_rmc_for_boms",
                args: {
                    bom_names: selected_boms
                },
                freeze: true,
                freeze_message: __("Calculating RCM for selected BOMs..."),
                callback: function(r) {
                    if (!r.message) {
                        return;
                    }

                    listview.clear_checked_items();
                    listview.refresh();

                    frappe.show_alert({
                        message: __("RCM calculated for {0} BOM(s).", [r.message.processed_boms.length]),
                        indicator: "green"
                    });
                }
            });
        });
    }
};
