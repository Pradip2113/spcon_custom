function set_district_filter(frm) {
    if (frm.doc.territory) {
        frm.call({
            method: "spcon.public.py.customer.set_territory_filter",
            args: {
                territory: frm.doc.territory,
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_query("custom_district", () => {
                        return {
                            filters: {
                                name: ["in", r.message]
                            }
                        };
                    });
                }
            }
        });
    }
}

frappe.ui.form.on("Customer", {
    onload_post_render: function(frm) {
        set_district_filter(frm);
    },
    territory: function(frm) {
        set_district_filter(frm);
    }
});
