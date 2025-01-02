def create_invoice(args: dict) -> dict:
    # e.g. amount, flight details, etc.
    print("[CreateInvoice] Creating invoice with:", args)
    return {
        "invoiceStatus": "generated",
        "invoiceURL": "https://pay.example.com/invoice/12345",
    }
