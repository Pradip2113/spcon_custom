// frappe.ui.form.on("Lead", {
//     custom_add_data(frm) {

//         frappe.db.get_doc("System", frm.doc.custom_system)
//             .then(system_doc => {
//               (system_doc.system_items || []).forEach(d => {
//                     let row = frm.add_child("custom_project_details_items");

//                     row.segment = frm.doc.custom_segment;
//                     row.scope_of_work = frm.doc.custom_scope_of_work;
//                     row.system = frm.doc.custom_system;
//                     row.area = frm.doc.custom_area;

//                     row.item = d.item_code;
//                     row.qty = (frm.doc.custom_area * d.qty);
//                 });

//                 frm.refresh_field("custom_project_details_items");

//                 // Clear fields
//                 frm.set_value("custom_scope_of_work", "");
//                 frm.set_value("custom_segment", "");
//                 frm.set_value("custom_system", "");
//                 frm.set_value("custom_area", "");

//                 // --- 2. Build unique item list with total qty ---
//                 let item_map = {};

//                 (frm.doc.custom_project_details_items || []).forEach(r => {
//                     if (!r.item) return;

//                     if (!item_map[r.item]) {
//                         item_map[r.item] = 0;
//                     }
//                     item_map[r.item] += (r.qty || 0);
//                 });

//                 // Clear existing rows (optional, but recommended)
//                 frm.clear_table("custom_project_items");

//                 // --- 3. Add unique items to custom_project_items ---
//                 Object.keys(item_map).forEach(item_code => {
//                     let item_row = frm.add_child("custom_project_items");
//                     item_row.item_code = item_code;
//                     item_row.total_qty = item_map[item_code];
//                 });

//                 frm.refresh_field("custom_project_items");
//             });
//     }
// });

frappe.ui.form.on("Lead", {
    custom_add_data: function(frm) {   
        let duplicate = frm.doc.custom_project_details_items.some(r =>
            r.segment === frm.doc.custom_segment &&
            r.scope_of_work === frm.doc.custom_scope_of_work &&
            r.system === frm.doc.custom_system &&
            r.area === frm.doc.custom_area
        );
        if (duplicate) {  
            frappe.msgprint("This data already exists!");
            return;
        }
        frappe.db.get_doc("System SPC", frm.doc.custom_system).then(system => {
            system.system_items_spc.forEach(item => {
                let row = frm.add_child("custom_project_details_items");
                row.segment = frm.doc.custom_segment;
                row.scope_of_work = frm.doc.custom_scope_of_work;
                row.system = frm.doc.custom_system;
                row.area = frm.doc.custom_area || 0; 
                row.item = item.item_code;
                row.qty = (frm.doc.custom_area || 0) * (item.qty || 0);  
            });
            frm.refresh_field("custom_project_details_items");
            // Clear input fields
            frm.set_value("custom_segment", "");
            frm.set_value("custom_scope_of_work", "");
            frm.set_value("custom_system", "");
            frm.set_value("custom_area", "");
            // Calculate total qty per item
            let totals = {};
            frm.doc.custom_project_details_items.forEach(r => {
                if (!totals[r.item]) totals[r.item] = 0;
                totals[r.item] += r.qty || 0;
            });
            frm.clear_table("custom_project_items"); 
            for (let item in totals) {
                let row = frm.add_child("custom_project_items");
                row.item_code = item;
                row.total_qty = totals[item];
            }
            frm.refresh_field("custom_project_items");
        });
    },
    refresh(frm) {
        frm.set_query('custom_scope_of_work', function () {
            return {
                filters: {
                    segment: frm.doc.custom_segment
                }
            };
        });

        frm.set_query('custom_system', function () {
            return {
                filters: {
                    scope_of_work: frm.doc.custom_scope_of_work
                }
            };
        });
    },
    custom_segment(frm) {
        // Clear scope of work when segment changes
        frm.set_value("custom_scope_of_work", null);
    }
});
