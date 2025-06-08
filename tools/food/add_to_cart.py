def add_to_cart(args: dict) -> dict:
    """
    Simple stateless cart tool for demo purposes.
    In production, this would use proper session storage or database.
    """
    customer_email = args.get("customer_email")
    item_name = args.get("item_name")
    item_price = float(args.get("item_price", 0))
    quantity = int(args.get("quantity", 1))
    stripe_product_id = args.get("stripe_product_id")
    
    # Basic validation
    if not customer_email:
        return {"error": "Customer email is required"}
    if not item_name:
        return {"error": "Item name is required"}
    if item_price <= 0:
        return {"error": "Item price must be greater than 0"}
    if quantity <= 0:
        return {"error": "Quantity must be greater than 0"}
    
    # For demo purposes, just acknowledge the addition
    # In a real system, this would store to session/database
    return {
        "status": "success",
        "message": f"Added {quantity} x {item_name} (${item_price}) to cart for {customer_email}",
        "item_added": {
            "name": item_name,
            "price": item_price,
            "quantity": quantity,
            "stripe_product_id": stripe_product_id
        }
    }