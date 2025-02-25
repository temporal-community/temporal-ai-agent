from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import time
import random
import string


def parse_datetime(datetime_str):
    # Remove trailing 'Z' if present
    if datetime_str.endswith("Z"):
        datetime_str = datetime_str[:-1]

    formats = [
        "%Y-%m-%dT%H:%M",  # e.g. "2025-04-18T09:00"
        "%Y-%m-%dT%H:%M:%S",  # e.g. "2025-04-18T09:00:00"
        "%Y-%m-%d %H:%M:%S",  # e.g. "2025-04-18 09:00:00"
        "%Y-%m-%d",  # e.g. "2025-04-11"
    ]

    for fmt in formats:
        try:
            parsed = time.strptime(datetime_str, fmt)
            if fmt == "%Y-%m-%d":
                # Default to 9am if no time provided
                hour, minute = 9, 0
            else:
                hour, minute = parsed.tm_hour, parsed.tm_min
            return (
                parsed.tm_year,
                parsed.tm_mon,
                parsed.tm_mday,
                hour,
                minute,
            )
        except ValueError:
            continue
    return None, None, None, None, None


class TrainServer(BaseHTTPRequestHandler):
    def generate_journeys(self, origin, destination, out_datetime, ret_datetime):
        journeys = []

        # Helper to format datetime
        def format_datetime(year, month, day, hour, minute):
            return "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}".format(
                year=year, month=month, day=day, hour=hour, minute=minute
            )

        # Generate outbound journeys
        year, month, day, hour, minute = out_datetime
        for offset in [-30, 0, 30]:
            # Calculate journey times
            adj_minutes = minute + offset
            adj_hour = hour + (adj_minutes // 60)
            adj_minute = adj_minutes % 60

            # Simple handling of day rollover
            adj_day = day + (adj_hour // 24)
            adj_hour = adj_hour % 24

            # Journey takes 2h15m-2h45m (135-165 minutes)
            duration = 135 + random.randint(0, 30)
            arr_hour = adj_hour + (duration // 60)
            arr_minute = (adj_minute + (duration % 60)) % 60
            arr_day = adj_day + (arr_hour // 24)
            arr_hour = arr_hour % 24

            journey = {
                "id": "T{}".format(random.randint(1000, 9999)),
                "type": "outbound",
                "departure": origin,
                "arrival": destination,
                "departure_time": format_datetime(
                    year, month, adj_day, adj_hour, adj_minute
                ),
                "arrival_time": format_datetime(
                    year, month, arr_day, arr_hour, arr_minute
                ),
                "price": round(30 + random.random() * 50, 2),
            }
            journeys.append(journey)

        # Generate return journeys if return datetime provided
        if ret_datetime[0] is not None:
            year, month, day, hour, minute = ret_datetime
            for offset in [-30, 0, 30]:
                adj_minutes = minute + offset
                adj_hour = hour + (adj_minutes // 60)
                adj_minute = adj_minutes % 60

                adj_day = day + (adj_hour // 24)
                adj_hour = adj_hour % 24

                # Journey takes 2h15m-2h45m (135-165 minutes)
                duration = 135 + random.randint(0, 30)
                arr_hour = adj_hour + (duration // 60)
                arr_minute = (adj_minute + (duration % 60)) % 60
                arr_day = adj_day + (arr_hour // 24)
                arr_hour = arr_hour % 24

                journey = {
                    "id": "T{}".format(random.randint(1000, 9999)),
                    "type": "return",
                    "departure": destination,
                    "arrival": origin,
                    "departure_time": format_datetime(
                        year, month, adj_day, adj_hour, adj_minute
                    ),
                    "arrival_time": format_datetime(
                        year, month, arr_day, arr_hour, arr_minute
                    ),
                    "price": round(30 + random.random() * 50, 2),
                }
                journeys.append(journey)

        return journeys

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/api/search":
            try:
                params = parse_qs(parsed_url.query)
                origin = params.get("from", [""])[0]
                destination = params.get("to", [""])[0]
                outbound_datetime = params.get("outbound_time", [""])[0]
                return_datetime = params.get("return_time", [""])[0]

                if not origin or not destination or not outbound_datetime:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {
                                "error": "Required parameters: 'from', 'to', and 'outbound_time'"
                            }
                        ).encode("utf-8")
                    )
                    return

                # Parse datetimes
                out_dt = parse_datetime(outbound_datetime)
                ret_dt = (
                    parse_datetime(return_datetime)
                    if return_datetime
                    else (None, None, None, None, None)
                )

                if out_dt[0] is None:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {"error": "Invalid datetime format. Use YYYY-MM-DDTHH:MM"}
                        ).encode("utf-8")
                    )
                    return

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                journeys = self.generate_journeys(origin, destination, out_dt, ret_dt)
                response = json.dumps({"journeys": journeys})

                self.wfile.write(response.encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path.startswith("/api/book/"):
            train_ids = parsed_url.path.split("/")[-1].split(",")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            booking_ref = "BR" + "".join(
                [random.choice(string.digits) for _ in range(5)]
            )

            response = json.dumps(
                {
                    "booking_reference": booking_ref,
                    "train_ids": train_ids,
                    "status": "confirmed",
                }
            )

            self.wfile.write(response.encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    server = HTTPServer(("", 8080), TrainServer)
    print("Train booking server starting on port 8080...")
    server.serve_forever()


if __name__ == "__main__":
    run_server()