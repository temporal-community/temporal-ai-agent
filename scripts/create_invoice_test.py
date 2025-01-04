from tools.create_invoice import create_invoice

if __name__ == "__main__":
    # Example usage:
    args_create = {
        "email": "jenny.rosen@example.com",
        "amount": 150.00,
        "description": "Flight to Seattle",
        "days_until_due": 7,
    }
    invoice_details = create_invoice(args_create)
    print(invoice_details)
