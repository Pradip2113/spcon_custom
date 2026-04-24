import frappe
from frappe.utils import flt

def validate_over_receipt_with_draft(doc, method=None):
    if not doc.items:
        return

    for item in doc.items:
        # ✅ FIXED FIELD NAME
        if not item.purchase_order or not item.purchase_order_item:
            continue

        # 🔹 Get PO Qty
        po_qty = frappe.db.get_value(
            "Purchase Order Item",
            item.purchase_order_item,
            "qty"
        ) or 0

        # 🔹 Get already received qty (DRAFT + SUBMITTED)
        received_qty = frappe.db.sql("""
            SELECT SUM(pri.qty)
            FROM `tabPurchase Receipt Item` pri
            JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
            WHERE pri.purchase_order_item = %s
            AND pr.docstatus IN (0, 1)
            AND pri.parent != %s
        """, (item.purchase_order_item, doc.name))[0][0] or 0

        # 🔹 Remaining qty
        remaining_qty = flt(po_qty) - flt(received_qty)

        # 🔹 Validation
        if flt(item.qty) > remaining_qty:
            frappe.throw(
                f"""Row #{item.idx} - Item <b>{item.item_code}</b><br>
                Remaining Qty: <b>{remaining_qty}</b><br>
                You cannot receive more than remaining quantity."""
            )