TREASURE_LOCATION = {
        "address": "300 Lenora",
        "city": "Seattle",
        "state_full": "Washington",
        "state_abbrev": "WA",
        "zip": "98121",
        "country": "USA"
}

HINTS = [
    "country of " + TREASURE_LOCATION["country"],
    "state of " + TREASURE_LOCATION["state_full"],
    "city of " + TREASURE_LOCATION["city"],
    "at a company HQ",
    "The company's tech traces its roots to a project called Cadence", #thanks, Grok
    "The company offers a tool that lets developers write code as if it's running forever, no matter what crashes", #thanks, Grok
]
''' Additional Grok provided hints about Temporal:
"This company was founded by two engineers who previously worked on a system named after a South American river at Uber."
"Their platform is all about orchestrating workflows that can survive failures—like a conductor keeping the music going."
"They offer a tool that lets developers write code as if it’s running forever, no matter what crashes."
"Their mission is tied to making distributed systems feel as simple as writing a single app."
"They’ve got a knack for ‘durability’—both in their software and their growing reputation."
"This outfit spun out of experiences at AWS and Uber, blending cloud and ride-sharing know-how."
"Their open-source framework has a community that’s ticking along, fixing bugs and adding features daily."
"They’re backed by big venture capital names like Sequoia, betting on their vision for reliable software."
"The company’s name might remind you of a word for something fleeting, yet their tech is built to last."'''

def give_hint(args: dict) -> dict:
    hint_total = args.get("hint_total")
    if hint_total is None:
        hint_total = 0
    
    index = hint_total % len(HINTS)
    hint_text = HINTS[index]

    hint_total = hint_total + 1
    return {
        "hint_number": hint_total,
        "hint": hint_text 
    }