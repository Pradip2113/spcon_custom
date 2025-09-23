import frappe

@frappe.whitelist()
def get_data(doc, method):
    po_items = frappe.get_all(
        "Purchase Order Item",
        filters={
            "material_request": doc.name,
            "docstatus": ["!=", 1]
        },
        fields=["parent"]
    )

    if po_items:
        links = ""
        for item in po_items:
            po_link = f'<a href="/app/purchase-order/{item["parent"]}" target="_blank">{item["parent"]}</a>'
            links += po_link + "<br>"

        frappe.throw(f"Material Request <b>{doc.name}</b> is already linked to Purchase Order(s):<br><br>{links}")
