def current_pto(args: dict) -> dict:
    
    email = args.get("email")
    if email == "bob.johnson@emailzzz.com":
        num_hours = 40
    else:
        num_hours = 20

    num_days = float(num_hours/8)

    return {
        "num_hours": num_hours,
        "num_days": num_days,
    }
