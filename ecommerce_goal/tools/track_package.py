import http
import os
import json

from pathlib import Path

#Send back dummy data in the correct format - to use the real API, 1) change this to be track_package_fake and 2) change the below track_package_real to be track_package 
def track_package(args: dict) -> dict:
    
    tracking_id = args.get("tracking_id")
    file_path = Path(__file__).resolve().parent.parent / "data" / "dummy_tracking_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}
    
    with open(file_path, "r") as file:
        data = json.load(file)
    package_list = data["packages"]

    for package in package_list:
        if package["TrackingNumber"] == tracking_id:
                scheduled_delivery_date = package["ScheduledDeliveryDate"]
                carrier = package["Carrier"]
                status_summary = package["StatusSummary"]
                tracking_details = package.get("TrackingDetails", [])
                last_tracking_update = ""
                if tracking_details and tracking_details is not None and tracking_details[0] is not None:
                    last_tracking_update = tracking_details[0]["EventDateTimeInDateTimeFormat"]
                
                tracking_link = ""
                if carrier == "USPS":
                    tracking_link = f"https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1={tracking_id}"
                elif carrier == "UPS":
                    tracking_link = f"https://www.ups.com/track?track=yes&trackNums={tracking_id}"

                return {
                    "scheduled_delivery_date": scheduled_delivery_date,
                    "carrier": carrier,
                    "status_summary": status_summary,
                    "tracking_link": tracking_link,
                    "last_tracking_update": last_tracking_update
                }
 
    return_msg = "Package not found with tracking info " + tracking_id
    return {"error": return_msg}

'''Format of response:
{
    "TrackingNumber": "",
    "Delivered": false,
    "Carrier": "USPS",
    "ServiceType": "USPS Ground Advantage<SUP>&#153;</SUP>",
    "PickupDate": "",
    "ScheduledDeliveryDate": "April 14, 2025",
    "ScheduledDeliveryDateInDateTimeFromat": "2025-04-14T00:00:00",
    "StatusCode": "In Transit from Origin Processing",
    "Status": "Departed Post Office",
    "StatusSummary": "Your item has left our acceptance facility and is in transit to a sorting facility on April 10, 2025 at 7:06 am in IRON RIDGE, WI 53035.",
    "Message": "",
    "DeliveredDateTime": "",
    "DeliveredDateTimeInDateTimeFormat": null,
    "SignatureName": "",
    "DestinationCity": "CITY",
    "DestinationState": "ST",
    "DestinationZip": "12345",
    "DestinationCountry": null,
    "EventDate": "2025-04-10T07:06:00",
    "TrackingDetails": [
        {
            "EventDateTime": "April 10, 2025 7:06 am",
            "Event": "Departed Post Office",
            "EventAddress": "IRON RIDGE WI 53035",
            "State": "WI",
            "City": "IRON RIDGE",
            "Zip": "53035",
            "EventDateTimeInDateTimeFormat": "2025-04-10T07:06:00"
        },
        {
            "EventDateTime": "April 9, 2025 11:29 am",
            "Event": "USPS picked up item",
            "EventAddress": "IRON RIDGE WI 53035",
            "State": "WI",
            "City": "IRON RIDGE",
            "Zip": "53035",
            "EventDateTimeInDateTimeFormat": "2025-04-09T11:29:00"
        },
        {
            "EventDateTime": "April 7, 2025 6:29 am",
            "Event": "Shipping Label Created, USPS Awaiting Item",
            "EventAddress": "IRON RIDGE WI 53035",
            "State": "WI",
            "City": "IRON RIDGE",
            "Zip": "53035",
            "EventDateTimeInDateTimeFormat": "2025-04-07T06:29:00"
        }
    ]
}
'''
def track_package_real(args: dict) -> dict:

    tracking_id = args.get("tracking_id")

    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST_PACKAGE", "trackingpackage.p.rapidapi.com")

    conn = http.client.HTTPSConnection(api_host)
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
        "Authorization": "Basic Ym9sZGNoYXQ6TGZYfm0zY2d1QzkuKz9SLw==",
    }

    path = f"/TrackingPackage?trackingNumber={tracking_id}"

    conn.request("GET", path, headers=headers)
    res = conn.getresponse()
    data = res.read()
    data_decoded = data.decode("utf-8")
    conn.close()

    try:
        json_data = json.loads(data_decoded)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response"}

    scheduled_delivery_date = json_data["ScheduledDeliveryDate"]
    carrier = json_data["Carrier"]
    status_summary = json_data["StatusSummary"]
    tracking_details = json_data.get("TrackingDetails", [])
    last_tracking_update = ""
    if tracking_details and tracking_details is not None and tracking_details[0] is not None:
        last_tracking_update = tracking_details[0]["EventDateTimeInDateTimeFormat"]
    tracking_link = ""
    if carrier == "USPS":
        tracking_link = f"https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1={tracking_id}"
    elif carrier == "UPS":
        tracking_link = f"https://www.ups.com/track?track=yes&trackNums={tracking_id}"

    return {
        "scheduled_delivery_date": scheduled_delivery_date,
        "carrier": carrier,
        "status_summary": status_summary,
        "tracking_link": tracking_link,
        "last_tracking_update": last_tracking_update
    }