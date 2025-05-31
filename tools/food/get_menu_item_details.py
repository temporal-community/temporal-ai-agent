from pathlib import Path
import json

def get_menu_item_details(args: dict) -> dict:
    item_id = args.get("item_id")
    restaurant_id = args.get("restaurant_id", "rest_001")
    
    file_path = Path(__file__).resolve().parent.parent / "data" / "food_ordering_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    
    restaurants = data["restaurants"]
    
    for restaurant in restaurants:
        if restaurant["id"] == restaurant_id:
            for item in restaurant["menu"]:
                if item["id"] == item_id:
                    return item
    
    return {"error": f"Menu item {item_id} not found."}