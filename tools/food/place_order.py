from pathlib import Path
import json
import uuid
from datetime import datetime, timedelta

def place_order(args: dict) -> dict:
    customer_email = args.get("customer_email")
    
    file_path = Path(__file__).resolve().parent.parent / "data" / "food_ordering_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    
    # Check if cart exists
    if customer_email not in data["carts"] or not data["carts"][customer_email]["items"]:
        return {"error": "Cart is empty. Please add items to cart first."}
    
    cart = data["carts"][customer_email]
    
    # Calculate total
    total = sum(item["price"] * item["quantity"] for item in cart["items"])
    
    # Create order
    order_id = f"order_{str(uuid.uuid4())[:8]}"
    order_date = datetime.now().isoformat() + "Z"
    estimated_delivery = (datetime.now() + timedelta(minutes=30)).isoformat() + "Z"
    
    new_order = {
        "id": order_id,
        "customer_email": customer_email,
        "restaurant_id": cart["restaurant_id"],
        "items": cart["items"],
        "total": round(total, 2),
        "status": "preparing",
        "order_date": order_date,
        "estimated_delivery": estimated_delivery
    }
    
    # Add order to data
    data["orders"].append(new_order)
    
    # Clear cart
    data["carts"][customer_email] = {"restaurant_id": cart["restaurant_id"], "items": []}
    
    # Save back to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    
    return {
        "status": "success",
        "order_id": order_id,
        "total": round(total, 2),
        "estimated_delivery": estimated_delivery,
        "message": "Order placed successfully!"
    }