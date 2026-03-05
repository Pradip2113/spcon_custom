import frappe
from frappe import _

@frappe.whitelist()
def calculate_rmc(doc):
    if isinstance(doc, str):
        doc = frappe.parse_json(doc)

    total_amount = 0

    for row in doc.get("items", []):

        if not row.get("item_code"):
            continue

        # Get default BOM from Item
        default_bom = frappe.db.get_value( "Item", row.get("item_code"), "default_bom")

        if not default_bom:
            continue

        # Get raw material cost from BOM
        raw_material_cost = frappe.db.get_value( "BOM", default_bom, "raw_material_cost") or 0

        qty = row.get("qty") or 0
        amount = raw_material_cost * qty

        # Update child row
        frappe.db.set_value(
            row.get("doctype"),
            row.get("name"),
            {
                "custom_rmc_cost": raw_material_cost,
                "custom_rmc_amount": amount
            }
        )

        total_amount += amount

    # ✅ Update Parent Fields
    quantity = doc.get("quantity") or 1

    frappe.db.set_value(
        "BOM",
        doc.get("name"),
        {
            "custom_final_product_amount": total_amount,
            "custom_single_unit_rate": total_amount / quantity
        }
    )

    return total_amount