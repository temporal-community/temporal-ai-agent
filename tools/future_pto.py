def future_pto(args: dict) -> dict:
    
    start_date = args.get("start_date")
    end_date = args.get("end_date")

    # get rate of accrual - need email?
    # get total hrs of PTO available as of start date (accrual * time between today and start date)
        # take into account other booked PTO??
    # calculate number of business hours of PTO: between start date and end date

    # enough_pto = total PTO as of start date - num biz hours of PTO > 0
    # pto_hrs_remaining_after = total PTO as of start date - num biz hours of PTO

    return {
        "enough_pto": True, 
        "pto_hrs_remaining_after": 410,
    }
