def book_pto(args: dict) -> dict:
    email = args.get("email")
    start_date = args.get("start_date")
    end_date = args.get("end_date")

    print(
        f"[BookPTO] Totally would send an email confirmation of PTO from {start_date} to {end_date} to {email} here!"
    )

    return {"status": "success"}
