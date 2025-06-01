import json
from datetime import date, datetime
from pathlib import Path

import pandas
from dateutil.relativedelta import relativedelta


def future_pto_calc(args: dict) -> dict:
    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "employee_pto_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    start_date = datetime.strptime(args.get("start_date"), "%Y-%m-%d").date()
    end_date = datetime.strptime(args.get("end_date"), "%Y-%m-%d").date()
    email = args.get("email")

    # Next, set up the ability to calculate how much PTO will be added to the user's total by the start of the PTO request
    today = date.today()

    if today > start_date:
        return_msg = (
            "PTO start date " + args.get("start_date") + "cannot be in the past"
        )
        return {"error": return_msg}

    if end_date < start_date:
        return_msg = (
            "PTO end date "
            + args.get("end_date")
            + " must be after PTO start date "
            + args.get("start_date")
        )
        return {"error": return_msg}

    # Get the number of business days, and then business hours (assume 8 hr biz day), included in the PTO request
    biz_days_of_request = len(
        pandas.bdate_range(start=start_date, end=end_date, inclusive="both")
    )
    if biz_days_of_request == 0:
        return_msg = (
            "There are no business days between "
            + args.get("start_date")
            + " and "
            + args.get("end_date")
        )
        return {"error": return_msg}
    biz_hours_of_request = biz_days_of_request * 8

    # Assume PTO is added on the first of every month - month math compares rolling dates, so compare the PTO request with the first day of the current month.
    today_first_of_month = date(today.year, today.month, 1)
    time_difference = relativedelta(start_date, today_first_of_month)
    months_to_accrue = time_difference.years * 12 + time_difference.months

    data = json.load(open(file_path))
    employee_list = data["theCompany"]["employees"]

    enough_pto = False

    for employee in employee_list:
        if employee["email"] == email:
            current_pto_hours = int(employee["currentPTOHrs"])
            hrs_added_per_month = int(employee["hrsAddedPerMonth"])
            pto_available_at_start = current_pto_hours + (
                months_to_accrue * hrs_added_per_month
            )
            pto_hrs_remaining_after = pto_available_at_start - biz_hours_of_request
            if pto_hrs_remaining_after >= 0:
                enough_pto = True
            return {
                "enough_pto": enough_pto,
                "pto_hrs_remaining_after": str(pto_hrs_remaining_after),
            }

    return_msg = "Employee not found with email address " + email
    return {"error": return_msg}
