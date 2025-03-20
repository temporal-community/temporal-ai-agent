from pathlib import Path
import json

# this is made to demonstrate functionality but it could just as durably be an API call
# this assumes it's a valid account - use check_account_valid() to verify that first
def get_account_balance(args: dict) -> dict:
    
    account_key = args.get("accountkey")

    file_path = Path(__file__).resolve().parent.parent / "data" / "customer_account_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    account_list = data["accounts"]

    for account in account_list:
        if account["email"] == account_key or account["account_id"] == account_key:
            #return{"status": "account valid"}
            return{ "name": account["name"], "email": account["email"], "account_id": account["account_id"], "checking_balance": account["checking_balance"], "savings_balance": account["savings_balance"], "bitcoin_balance": account["bitcoin_balance"], "account_creation_date": account["account_creation_date"] }
        
    return_msg = "Account not found with email address " + email + " or account ID: " + account_id
    return {"error": return_msg}