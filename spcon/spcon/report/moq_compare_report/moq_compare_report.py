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

    finished_goods_groups = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": "Finished Goods"},
        pluck="name"
    )

    if not finished_goods_groups:
        return columns, []

    item_filters = {
        "item_group": ["in", finished_goods_groups],
        **({"name": filters.item_code} if filters and filters.item_code else {})
    }

    items = frappe.get_all(
        "Item",
        filters=item_filters,
        fields=["name", "item_name", "custom_minimum_sale_qty"],
        order_by="name"
    )

    if not items:
        return columns, []

    item_codes = [item.name for item in items]
    bin_filters = {
        "item_code": ["in", item_codes],
        **({"warehouse": filters.warehouse} if filters and filters.warehouse else {})
    }

    bins = frappe.get_all(
        "Bin",
        filters=bin_filters,
        fields=["item_code", "warehouse", "actual_qty"],
        order_by="item_code, warehouse"
    )

    bins_by_item = {}
    for row in bins:
        bins_by_item.setdefault(row.item_code, []).append(row)

    data = []

    for item in items:
        item_bins = bins_by_item.get(item.name) or [None]

        for index, row in enumerate(item_bins):
            data.append({
                "item_code": item.name if index == 0 else "",
                "item_name": item.item_name,
                "warehouse": row.warehouse if row else (filters.warehouse if filters and filters.warehouse else ""),
                "available_qty": row.actual_qty if row else 0,
                "moq": item.custom_minimum_sale_qty or 0
            })

    return columns, data
