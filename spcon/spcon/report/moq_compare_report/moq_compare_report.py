# Copyright (c) 2026, Sanpra and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = [
        {
            "label": "Item Code",
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Warehouse",
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 180
        },
        {
            "label": "Available Qty",
            "fieldname": "available_qty",
            "fieldtype": "Float",
            "width": 120
        },
        {
            "label": "MOQ",
            "fieldname": "moq",
            "fieldtype": "Float",
            "width": 100
        }
    ]

    bins = frappe.get_all(
        "Bin",
        filters={
            "actual_qty": [">", 0],
            **({"item_code": filters.item_code} if filters and filters.item_code else {}),
            **({"warehouse": filters.warehouse} if filters and filters.warehouse else {})
        },
        fields=[
            "item_code",
            "warehouse",
            "actual_qty"
        ],
        order_by="item_code"
    )

    data = []
    added_items = set()

    for row in bins:

        item = frappe.db.get_value(
            "Item",
            row.item_code,
            ["item_name", "custom_minimum_sale_qty"],
            as_dict=True
        )

        # Show Item Code only for first row
        item_code = row.item_code if row.item_code not in added_items else ""

        data.append({
            "item_code": item_code,
            "item_name": item.item_name,
            "warehouse": row.warehouse,
            "available_qty": row.actual_qty,
            "moq": item.custom_minimum_sale_qty or 0
        })

        added_items.add(row.item_code)

    return columns, data