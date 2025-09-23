// // Copyright (c) 2025, Sanpra and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("District", {
// // 	refresh(frm) {

// // 	},
// // });
//  frappe.ui.form.on("District", {
//     refresh(frm) {
//         frm.add_custom_button("Set Permission", () => {
//             frappe.call({
//                 method: "frappe.client.get_list",
//                 args: {
//                     doctype: "DocType",
//                     fields: ["name"],
//                     limit_page_length: 1000
//                 },
//                 callback: function (res) {
//                     if (res.message) {
//                         const all_docs = res.message.map(d => d.name);

//                         // Process in batches of 50
//                         for (let i = 0; i < all_docs.length; i += 50) {
//                             let batch = all_docs.slice(i, i + 50);

//                             frappe.call({
//                                 method: "spcon.spcon.doctype.district.district.add",
//                                 args: { doctypes: JSON.stringify(batch) },
//                                 freeze: true,
//                                 callback: (r) => {
//                                     console.log("Processed batch:", batch);
//                                 }
//                             });
//                         }
//                     }
//                 }
//             });
//         });
//     },
// });
