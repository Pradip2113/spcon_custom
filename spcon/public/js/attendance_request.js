frappe.ui.form.on('Attendance Request', {
    refresh(frm) {
        // On reload, re-hide buttons if times already set
        if (frm.doc.custom_out_time) {
            frm.set_df_property('custom_add_out_time', 'hidden', 1);
        }
        if (frm.doc.custom_in_time) {
            frm.set_df_property('custom_add_in_time', 'hidden', 1);
        }
    },

    // Employee goes out 
    custom_add_out_time(frm) {
        let now = frappe.datetime.now_time(); // HH:mm:ss
        frm.set_value('custom_out_time', now);
        frm.set_df_property('custom_add_out_time', 'hidden', 1);
    },

    // Employee comes back (CALCULATE HERE)
    custom_add_in_time(frm) {
        if (!frm.doc.custom_out_time) {
            frappe.msgprint("Please add Out Time first");
            return;
        }

        let now = frappe.datetime.now_time();
        frm.set_value('custom_in_time', now);
        frm.set_df_property('custom_add_in_time', 'hidden', 1);
        
        setTimeout(() => {
            apply_half_day_rule(frm);
        }, 200);
    }
});

function apply_half_day_rule(frm) {
    if (!frm.doc.custom_out_time || !frm.doc.custom_in_time) {
        return;
    }

    const formats = ["HH:mm:ss", "HH:mm"];
    const out_m = moment(frm.doc.custom_out_time, formats, true);
    const in_m = moment(frm.doc.custom_in_time, formats, true);
    if (!out_m.isValid() || !in_m.isValid()) return;

    let diff_minutes = in_m.diff(out_m, "minutes");
    if (diff_minutes < 0) diff_minutes += 24 * 60;

    // ✅ RULE:
    // more than 30 minutes AND up to 4 hours (240 minutes)
    if (diff_minutes > 30 && diff_minutes <= 240 && frm.doc.custom_purpose == "Personal Work") {
        frm.set_value('half_day', 1);
        frm.set_value('half_day_date', frm.doc.from_date);
        frm.set_df_property('half_day', 'read_only', 1);
    } else {
        frm.set_value('half_day', 0);
    }
}
