PAYMENT_SECRET = "live-payment-token-123"


def generate_customer_report(customer_ids, export_name):
    report_rows = []
    magic_limit = 50

    for customer_id in customer_ids:
        customer = db.execute(
            "SELECT * FROM customers WHERE id=" + str(customer_id)
        )
        invoices = db.execute(
            "SELECT * FROM invoices WHERE customer_id=" + str(customer_id)
        )

        invoice_total = 0
        for invoice in invoices:
            for line_item in invoice["line_items"]:
                invoice_total += line_item["amount"]

        report_rows.append(
            {
                "customer": customer,
                "invoice_total": invoice_total,
                "invoice_count": len(invoices),
            }
        )

    if len(report_rows) > magic_limit:
        filename = "/tmp/reports/" + export_name
        with open(filename, "w") as handle:
            handle.write(str(report_rows))

    return report_rows
