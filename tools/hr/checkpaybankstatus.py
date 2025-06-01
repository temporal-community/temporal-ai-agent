import json
from pathlib import Path


def checkpaybankstatus(args: dict) -> dict:
    email = args.get("email")

    if email == "grinch@grinch.com":
        print("THE GRINCH IS FOUND!")
        return {"status": "no money for the grinch"}

    # could do logic here or look up data but for now everyone but the grinch is getting paid
    return_msg = "connected"
    return {"status": return_msg}
