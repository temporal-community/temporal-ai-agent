import http
import os
import json

def track_package_faked(args: dict) -> dict:
    
    tracking_id = args.get("tracking_id")
 
    #return_msg = "Account not found with email address " + email + " or account ID: " + account_id
    return {"tracking_info": "delivered, probably"}

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
def track_package(args: dict) -> dict:

    tracking_id = args.get("tracking_id")

    api_key = os.getenv("PACKAGE_RAPIDAPI_KEY")
    api_host = os.getenv("PACKAGE_RAPIDAPI_HOST", "trackingpackage.p.rapidapi.com")

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
    tracking_link = ""
    if carrier == "USPS":
        tracking_link = f"https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1={tracking_id}"
    #tracking_details = json_data.get("TrackingDetails", [])

    return {
        "scheduled_delivery_date": scheduled_delivery_date,
        "carrier": carrier,
        "status_summary": status_summary,
        "tracking_link": tracking_link,
    }