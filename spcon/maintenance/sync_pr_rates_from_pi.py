from collections import defaultdict

import frappe
from frappe.utils import flt

from erpnext.controllers.stock_controller import create_item_wise_repost_entries
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import update_billing_percentage


COMPANY = "SP Concare Private Limited"
FROM_DATE = "2025-04-01"
TO_DATE = "2026-03-31"
MANUFACTURING_PURPOSES = (
    "Manufacture",
    "Material Transfer for Manufacture",
    "Material Consumption for Manufacture",
)


def get_pr_item_rate_changes(from_date=FROM_DATE, to_date=TO_DATE, purchase_receipt=None):
    filters = {
        "company": COMPANY,
        "from_date": from_date,
        "to_date": to_date,
    }
    pr_filter = ""
    if purchase_receipt:
        filters["purchase_receipt"] = purchase_receipt
        pr_filter = "and pr.name = %(purchase_receipt)s"

    return frappe.db.sql(
        f"""
        select
            linked.purchase_receipt,
            linked.posting_date,
            linked.pr_detail,
            linked.item_code,
            linked.pr_qty,
            linked.pr_stock_qty,
            linked.current_pr_rate,
            linked.current_pr_base_rate,
            linked.current_pr_amount,
            linked.current_pr_base_amount,
            sum(linked.pi_qty) as pi_qty,
            sum(linked.pi_stock_qty) as pi_stock_qty,
            sum(linked.pi_amount) / nullif(sum(linked.pi_qty), 0) as pi_rate,
            sum(linked.pi_base_amount) / nullif(sum(linked.pi_qty), 0) as pi_base_rate,
            sum(linked.pi_amount) as pi_amount,
            sum(linked.pi_base_amount) as pi_base_amount,
            group_concat(distinct linked.purchase_invoice order by linked.purchase_invoice separator ', ') as purchase_invoices
        from (
            select
                pr.name as purchase_receipt,
                pr.posting_date,
                pri.name as pr_detail,
                pri.item_code,
                pri.qty as pr_qty,
                pri.stock_qty as pr_stock_qty,
                pri.rate as current_pr_rate,
                pri.base_rate as current_pr_base_rate,
                pri.amount as current_pr_amount,
                pri.base_amount as current_pr_base_amount,
                pii.qty as pi_qty,
                pii.stock_qty as pi_stock_qty,
                pii.amount as pi_amount,
                pii.base_amount as pi_base_amount,
                pi.name as purchase_invoice
            from `tabPurchase Receipt` pr
            inner join `tabPurchase Receipt Item` pri on pri.parent = pr.name
            inner join `tabPurchase Invoice Item` pii on pii.pr_detail = pri.name
            inner join `tabPurchase Invoice` pi on pi.name = pii.parent
            left join `tabSupplier` supplier on supplier.name = pr.supplier
            left join `tabSupplier` pi_supplier on pi_supplier.name = pi.supplier
            where pr.docstatus = 1
                and pi.docstatus = 1
                and pr.company = %(company)s
                and pr.posting_date between %(from_date)s and %(to_date)s
                and coalesce(pr.is_internal_supplier, 0) = 0
                and coalesce(pr.inter_company_reference, '') = ''
                and coalesce(pi.is_internal_supplier, 0) = 0
                and coalesce(pi.inter_company_invoice_reference, '') = ''
                and coalesce(supplier.is_internal_supplier, 0) = 0
                and coalesce(supplier.represents_company, '') = ''
                and coalesce(pi_supplier.is_internal_supplier, 0) = 0
                and coalesce(pi_supplier.represents_company, '') = ''
                {pr_filter}

            union all

            select
                pr.name as purchase_receipt,
                pr.posting_date,
                pri.name as pr_detail,
                pri.item_code,
                pri.qty as pr_qty,
                pri.stock_qty as pr_stock_qty,
                pri.rate as current_pr_rate,
                pri.base_rate as current_pr_base_rate,
                pri.amount as current_pr_amount,
                pri.base_amount as current_pr_base_amount,
                pii.qty as pi_qty,
                pii.stock_qty as pi_stock_qty,
                pii.amount as pi_amount,
                pii.base_amount as pi_base_amount,
                pi.name as purchase_invoice
            from `tabPurchase Receipt` pr
            inner join `tabPurchase Receipt Item` pri on pri.parent = pr.name
            inner join `tabPurchase Invoice Item` pii on pii.name = pri.purchase_invoice_item
            inner join `tabPurchase Invoice` pi on pi.name = pii.parent
            left join `tabSupplier` supplier on supplier.name = pr.supplier
            left join `tabSupplier` pi_supplier on pi_supplier.name = pi.supplier
            where pr.docstatus = 1
                and pi.docstatus = 1
                and pr.company = %(company)s
                and pr.posting_date between %(from_date)s and %(to_date)s
                and coalesce(pr.is_internal_supplier, 0) = 0
                and coalesce(pr.inter_company_reference, '') = ''
                and coalesce(pi.is_internal_supplier, 0) = 0
                and coalesce(pi.inter_company_invoice_reference, '') = ''
                and coalesce(supplier.is_internal_supplier, 0) = 0
                and coalesce(supplier.represents_company, '') = ''
                and coalesce(pi_supplier.is_internal_supplier, 0) = 0
                and coalesce(pi_supplier.represents_company, '') = ''
                and coalesce(pri.purchase_invoice_item, '') != ''
                {pr_filter}
        ) linked
        group by linked.pr_detail
        having coalesce(pi_rate, 0) > 0
            and (
                abs(coalesce(pi_rate, 0) - coalesce(current_pr_rate, 0)) > 0.0001
                or abs(coalesce(pi_qty, 0) - coalesce(pr_qty, 0)) > 0.0001
                or abs(coalesce(pi_stock_qty, 0) - coalesce(pr_stock_qty, 0)) > 0.0001
            )
        order by linked.posting_date, linked.purchase_receipt
        """,
        filters,
        as_dict=True,
    )

def get_manufacturing_usage(change):
    return frappe.db.sql(
        """
        select
            se.name as stock_entry,
            se.posting_date,
            se.purpose,
            sed.name as stock_entry_detail,
            sed.item_code,
            sed.qty,
            sed.basic_rate,
            sed.valuation_rate,
            sed.basic_amount,
            sed.amount
        from `tabStock Entry Detail` sed
        inner join `tabStock Entry` se on se.name = sed.parent
        where se.docstatus = 1
            and se.company = %s
            and se.purpose in %s
            and sed.item_code = %s
            and sed.s_warehouse is not null
            and se.posting_date >= %s
        order by se.posting_date, se.name, sed.idx
        """,
        (COMPANY, MANUFACTURING_PURPOSES, change.item_code, change.posting_date),
        as_dict=True,
    )


def collect_changes(from_date=FROM_DATE, to_date=TO_DATE, purchase_receipt=None, include_usage=False):
    changes = get_pr_item_rate_changes(from_date, to_date, purchase_receipt)
    if include_usage:
        for change in changes:
            change.manufacturing_usage = get_manufacturing_usage(change)
    return changes


def apply_pr_rate_change(doc, change):
    item = next((row for row in doc.items if row.name == change.pr_detail), None)
    if not item:
        return

    item.qty = flt(change.pi_qty, item.precision("qty"))
    item.received_qty = item.qty
    item.stock_qty = flt(change.pi_stock_qty, item.precision("stock_qty"))
    item.received_stock_qty = item.stock_qty
    if item.qty:
        item.conversion_factor = flt(item.stock_qty / item.qty, item.precision("conversion_factor"))

    item.rate = flt(change.pi_rate, item.precision("rate"))
    item.base_rate = flt(change.pi_base_rate, item.precision("base_rate"))
    item.price_list_rate = item.rate
    item.base_price_list_rate = item.base_rate
    item.discount_percentage = 0
    item.discount_amount = 0
    item.margin_type = ""
    item.margin_rate_or_amount = 0
    item.net_rate = item.rate
    item.base_net_rate = item.base_rate
    item.amount = flt(change.pi_amount, item.precision("amount"))
    item.base_amount = flt(change.pi_base_amount, item.precision("base_amount"))
    item.net_amount = item.amount
    item.base_net_amount = item.base_amount


def apply(from_date=FROM_DATE, to_date=TO_DATE, purchase_receipt=None):
    changes = collect_changes(from_date, to_date, purchase_receipt)
    changes_by_pr = defaultdict(list)
    for change in changes:
        changes_by_pr[change.purchase_receipt].append(change)

    print_summary("apply", changes)

    repost_count = 0
    for pr_name in sorted(changes_by_pr):
        doc = frappe.get_doc("Purchase Receipt", pr_name)
        for change in changes_by_pr[pr_name]:
            apply_pr_rate_change(doc, change)

        if hasattr(doc, "calculate_taxes_and_totals"):
            doc.calculate_taxes_and_totals()
        update_billing_percentage(doc, update_modified=False, adjust_incoming_rate=True)
        doc.update_valuation_rate(reset_outgoing_rate=False)

        doc.db_update()
        for item in doc.items:
            item.db_update()
        for tax in doc.get("taxes", []):
            tax.db_update()

        repost_count += len(create_item_wise_repost_entries("Purchase Receipt", pr_name))

    frappe.db.commit()
    print(f"updated_pr_items: {len(changes)}")
    print(f"updated_purchase_receipts: {len(changes_by_pr)}")
    print(f"created_repost_entries: {repost_count}")


def dry_run(from_date=FROM_DATE, to_date=TO_DATE, purchase_receipt=None, show_usage=False):
    changes = collect_changes(from_date, to_date, purchase_receipt, include_usage=show_usage)
    print_summary("dry-run", changes, show_usage=show_usage)
    frappe.db.rollback()


def print_summary(mode, changes, show_usage=False):
    print(f"mode: {mode}")
    print(f"change_rows: {len(changes)}")
    print(f"purchase_receipts: {len(set(row.purchase_receipt for row in changes))}")
    print("top_changes:")
    for row in sorted(
        changes,
        key=lambda d: (
            abs(flt(d.pi_rate) - flt(d.current_pr_rate))
            + abs(flt(d.pi_qty) - flt(d.pr_qty))
            + abs(flt(d.pi_stock_qty) - flt(d.pr_stock_qty))
        ),
        reverse=True,
    )[:50]:
        print(
            f"{row.posting_date} {row.purchase_receipt} {row.item_code} "
            f"pr_qty={flt(row.pr_qty):.6f} pi_qty={flt(row.pi_qty):.6f} "
            f"pr_rate={flt(row.current_pr_rate):.6f} pi_rate={flt(row.pi_rate):.6f} "
            f"invoices={row.purchase_invoices}"
        )
        if show_usage:
            usage = row.get("manufacturing_usage") or []
            print(f"  manufacturing_rows_after_pr: {len(usage)}")
            for used in usage[:10]:
                print(
                    f"  {used.posting_date} {used.stock_entry} {used.purpose} "
                    f"rate={flt(used.basic_rate):.6f} valuation={flt(used.valuation_rate):.6f}"
                )
