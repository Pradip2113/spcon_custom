# import frappe
# from frappe import _

# @frappe.whitelist()
# def calculate_rmc(doc):
#     if isinstance(doc, str):
#         doc = frappe.parse_json(doc)

#     total_amount = 0

#     for row in doc.get("items", []):

#         if not row.get("item_code"):
#             continue

#         # Get default BOM from Item
#         default_bom = frappe.db.get_value( "Item", row.get("item_code"), "default_bom")

#         if not default_bom:
#             continue

#         # Get raw material cost from BOM
#         raw_material_cost = frappe.db.get_value( "BOM", default_bom, "raw_material_cost") or 0

#         qty = row.get("qty") or 0
#         amount = raw_material_cost * qty

#         # Update child row
#         frappe.db.set_value(
#             row.get("doctype"),
#             row.get("name"),
#             {
#                 "custom_rmc_cost": raw_material_cost,
#                 "custom_rmc_amount": amount
#             }
#         )

#         total_amount += amount

#     # ✅ Update Parent Fields
#     quantity = doc.get("quantity") or 1

#     frappe.db.set_value(
#         "BOM",
#         doc.get("name"),
#         {
#             "custom_final_product_amount": total_amount,
#             "custom_single_unit_rate": total_amount / quantity
#         }
#     )

#     return total_amount





import frappe
from frappe import _


def _calculate_rmc_for_doc(doc):
    total_amount = 0
    updated_rows = []

    for row in doc.get("items", []):
        if not row.get("item_code"):
            continue

        qty = row.get("qty") or 0
        rmc_cost = row.get("custom_rmc_cost") or 0
        amount = qty * rmc_cost

        frappe.db.set_value(
            row.get("doctype"),
            row.get("name"),
            "custom_rmc_amount",
            amount
        )

        updated_rows.append({
            "name": row.get("name"),
            "amount": amount
        })
        total_amount += amount

    quantity = doc.get("quantity") or 1
    single_rate = total_amount / quantity

    frappe.db.set_value("BOM", doc.get("name"), {
        "custom_final_product_amount": total_amount,
        "custom_single_unit_rate": single_rate
    })

    return {
        "rows": updated_rows,
        "total": total_amount,
        "rate": single_rate
    }


@frappe.whitelist()
def calculate_rmc(doc):
    if isinstance(doc, str):
        doc = frappe.parse_json(doc)

    return _calculate_rmc_for_doc(doc)


@frappe.whitelist()
def calculate_rmc_for_boms(bom_names):
    if isinstance(bom_names, str):
        bom_names = frappe.parse_json(bom_names)

    if not bom_names:
        frappe.throw(_("Please select at least one BOM."))

    processed_boms = []

    for bom_name in bom_names:
        doc = frappe.get_doc("BOM", bom_name)
        _calculate_rmc_for_doc(doc)
        processed_boms.append(bom_name)

    return {
        "processed_boms": processed_boms
    }
