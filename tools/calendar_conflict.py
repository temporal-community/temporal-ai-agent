def calendar_conflict(args: dict) -> dict:
    
    check_self = args.get("check_self_calendar")
    check_team = args.get("check_team_calendar")

    conflict_list = []
    conflict = {
        "calendar": "self",
        "title": "Meeting with Karen",
        "date": "2025-12-02",
        "time": "10:00AM",
    }
    conflict_list.append(conflict)

    return {
        "conflicts": conflict_list,
    }
