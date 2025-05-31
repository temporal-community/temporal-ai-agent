from pathlib import Path
import json

def add_to_cart(args: dict) -> dict:
    customer_email = args.get("customer_email")
    item_id = args.get("item_id")
    quantity = int(args.get("quantity", 1))
    restaurant_id = args.get("restaurant_id", "rest_001")
    
    file_path = Path(__file__).resolve().parent.parent / "data" / "food_ordering_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    
    # Find the item to get its price
    item_price = None
    item_name = None
    for restaurant in data["restaurants"]:
        if restaurant["id"] == restaurant_id:
            for item in restaurant["menu"]:
                if item["id"] == item_id:
                    item_price = item["price"]
                    item_name = item["name"]
                    break
    
    if item_price is None:
        return {"error": f"Item {item_id} not found."}
    
    # Initialize cart if it doesn't exist
    if customer_email not in data["carts"]:
        data["carts"][customer_email] = {
            "restaurant_id": restaurant_id,
            "items": []
        }
    
    # Check if item already in cart
    cart = data["carts"][customer_email]
    existing_item = None
    for cart_item in cart["items"]:
        if cart_item["item_id"] == item_id:
            existing_item = cart_item
            break
    
    if existing_item:
        existing_item["quantity"] += quantity
    else:
        cart["items"].append({
            "item_id": item_id,
            "quantity": quantity,
            "price": item_price
        })
    
    # Save back to file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    
    return {
        "status": "success",
        "message": f"Added {quantity} x {item_name} to cart",
        "cart": cart
    }