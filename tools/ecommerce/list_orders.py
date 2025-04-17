from pathlib import Path
import json

def sorting(e):
  return e['order_date']

def list_orders(args: dict) -> dict:
    
    email_address = args.get("email_address")

    file_path = Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    order_list = data["orders"]

    rtn_order_list = []
    for order in order_list:
        if order["email"] == email_address:
            rtn_order_list.append(order)

    if len(rtn_order_list) > 0:
        rtn_order_list.sort(key=sorting)
        return {"orders": rtn_order_list}
    else:    
        return_msg = "No orders for customer " + email_address + " found."
        return {"error": return_msg}

