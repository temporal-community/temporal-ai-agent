from .give_hint import TREASURE_LOCATION

def guess_location(args: dict) -> dict:
    
    guess_address = args.get("address").lower()
    guess_city = args.get("city").lower()
    guess_state = args.get("state").lower()

    if len(guess_state) == 2:
        compare_state = TREASURE_LOCATION.get("state_abbrev").lower()
    else:
        compare_state = TREASURE_LOCATION.get("state_full").lower()

    #Check for the street address to be included in the guess to account for "st" vs "street" or leaving Street off entirely
    if TREASURE_LOCATION.get("address").lower() in guess_address and TREASURE_LOCATION.get("city").lower() == guess_city and compare_state == guess_state:
        return {"treasure_found": "True"}
    else:
        return {"treasure_found": "False"}