from pathlib import Path
import json

def get_menu(args: dict) -> dict:
    restaurant_id = args.get("restaurant_id", "rest_001")
    
    file_path = Path(__file__).resolve().parent.parent / "data" / "food_ordering_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    
    restaurants = data["restaurants"]
    
    for restaurant in restaurants:
        if restaurant["id"] == restaurant_id:
            return {
                "restaurant_name": restaurant["name"],
                "menu": restaurant["menu"]
            }
    
    return {"error": f"Restaurant {restaurant_id} not found."}