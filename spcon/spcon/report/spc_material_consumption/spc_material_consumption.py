# Copyright (c) 2025, Sanpra and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)  
	return columns, data


def get_columns():
    return [
        # {"label": "BOM No", "fieldname": "bom_no", "fieldtype": "Link", "options": "BOM", "width": 150},
        {"label": "Finish Item Code", "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 150},
        # {"label": "Parent Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 180},
        {"label": "BOM Qty", "fieldname": "bom_qty", "fieldtype": "Float", "width": 120},
        {"label": "Child Item Code", "fieldname": "child_item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Child Item Name", "fieldname": "child_item_name", "fieldtype": "Data", "width": 180},
		{"label": "Child Item UOM", "fieldname": "child_uom", "fieldtype": "Link", "options": "UOM",},
        {"label": "Child Qty", "fieldname": "child_qty", "fieldtype": "Float", "width": 120},
		{"label": "Child Rate", "fieldname": "child_rate", "fieldtype": "Float", "width": 120, "precision": 2},
		# {"label": "Child Qty per 1 Parent","fieldname": "child_per_unit","fieldtype": "Float","width": 160}

    ]


def get_data(filters):

    filter = {"is_active": 1}

    if filters.get("item_code"):
        filter["item"] = filters.get("item_code")

    data = []

    all_boms = frappe.get_all(
        "BOM",
        filters=filter,
        fields=["name", "item", "item_name", "quantity"]
    )

    for bom in all_boms:

        bom_items = frappe.get_all(
            "BOM Item",
            filters={"parent": bom.name},
            fields=["item_code", "item_name", "qty","uom", "rate"],
            order_by="idx asc"
        )

        first_row = True

        for child in bom_items:

            # Calculate child required for 1 Qty of parent
            child_per_unit = child.qty / bom.quantity if bom.quantity else 0

            if first_row:
                data.append({
                    # "bom_no": bom.name,
                    "item": bom.item,
                    "bom_qty": bom.quantity,
                    "child_item_code": child.item_code,
                    "child_item_name": child.item_name,
					"child_uom": child.uom,
                    "child_qty": child.qty,
                    "child_rate": child.rate,
                    # "child_per_unit": child_per_unit,
                })
                first_row = False
            else:
                data.append({
                    # "bom_no": "",
                    "item": "",
                    "bom_qty": "",
                    "child_item_code": child.item_code,
                    "child_item_name": child.item_name,
					"child_uom": child.uom,
                    "child_qty": child.qty,
                    "child_rate": child.rate,
                    # "child_per_unit": child_per_unit,
                })

    return data
