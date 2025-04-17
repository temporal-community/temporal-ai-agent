from pathlib import Path
import json

# this is made to demonstrate functionality but it could just as durably be an API call
# called as part of a temporal activity with automatic retries
def get_order(args: dict) -> dict:
    
    order_id = args.get("order_id")

    file_path = Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    order_list = data["orders"]

    for order in order_list:
        if order["id"] == order_id:
            return order
        
    return_msg = "Order " + order_id + " not found."
    return {"error": return_msg}