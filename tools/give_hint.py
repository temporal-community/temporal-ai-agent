TREASURE_LOCATION = {
        "address": "300 Lenora",
        "city": "Seattle",
        "state_full": "Washington",
        "state_abbrev": "WA",
        "zip": "98121",
        "country": "USA"
}

HINTS = [
    "state of Washington",
    "city of Seattle",
    "at a company HQ",
]
''' Grok provided hints:
Here are additional company-specific clues about Temporal that could help players in your game guess the address (300 Lenora St, Seattle, WA) by focusing on the company itself. These are designed to be intriguing and game-friendly:

"This company was founded by two engineers who previously worked on a system named after a South American river at Uber."
"Their platform is all about orchestrating workflows that can survive failures—like a conductor keeping the music going."
"They offer a tool that lets developers write code as if it’s running forever, no matter what crashes."
"The company’s tech traces its roots to a project called Cadence, which they took to the next level."
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

    print(f"hint_total: {hint_total}, length: {len(HINTS)}, index: {index}")
    hint_total = hint_total + 1
    return {
        "hint_number": hint_total,
        "hint": hint_text 
    }