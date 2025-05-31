from pathlib import Path
import json

def check_order_status(args: dict) -> dict:
    order_id = args.get("order_id")
    
    file_path = Path(__file__).resolve().parent.parent / "data" / "food_ordering_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    
    orders = data["orders"]
    
    for order in orders:
        if order["id"] == order_id:
            return {
                "order_id": order["id"],
                "status": order["status"],
                "order_date": order["order_date"],
                "estimated_delivery": order["estimated_delivery"],
                "actual_delivery": order.get("actual_delivery"),
                "total": order["total"],
                "items": order["items"]
            }
    
    return {"error": f"Order {order_id} not found."}