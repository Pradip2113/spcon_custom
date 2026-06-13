// (function () {
// 	const RATE_FIELDS = ["incoming_rate", "in_out_rate", "valuation_rate"];

// 	function apply_stock_ledger_rate_precision(columns) {
// 		if (!Array.isArray(columns)) {
// 			return columns;
// 		}

// 		columns.forEach((column) => {
// 			if (column && RATE_FIELDS.includes(column.fieldname)) {
// 				column.precision = 5;
// 			}
// 		});

// 		return columns;
// 	}

// 	function patch_query_report() {
// 		if (!frappe.views?.QueryReport?.prototype) {
// 			setTimeout(patch_query_report, 200);
// 			return;
// 		}

// 		const prototype = frappe.views.QueryReport.prototype;
// 		if (prototype._spcon_stock_ledger_precision_patched) {
// 			return;
// 		}

// 		const original_prepare_columns = prototype.prepare_columns;
// 		prototype.prepare_columns = function (columns) {
// 			if (this.report_name === "Stock Ledger") {
// 				apply_stock_ledger_rate_precision(columns);
// 			}

// 			return original_prepare_columns.call(this, columns);
// 		};

// 		prototype._spcon_stock_ledger_precision_patched = true;
// 	}

// 	frappe.ready(patch_query_report);
// })();
