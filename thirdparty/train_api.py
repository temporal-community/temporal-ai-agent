# Version-compatible imports
try:
    # Modern Python
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import parse_qs, urlparse
    import json
except ImportError:
    # Python 1.5.2
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from urlparse import parse_qs, urlparse

import time
import random
import string


def parse_datetime(datetime_str):
    # Parse YYYY-MM-DDTHH:MM format
    try:
        date_part, time_part = datetime_str.split('T')
        year, month, day = map(int, date_part.split('-'))
        hour, minute = map(int, time_part.split(':'))
        return year, month, day, hour, minute
    except:
        return None, None, None, None, None


class TrainServer(BaseHTTPRequestHandler):
    def format_json(self, obj):
        # Simple JSON-like string formatter for 1.5.2 compatibility
        try:
            return json.dumps(obj)
        except NameError:
            if isinstance(obj, dict):
                pairs = []
                for k, v in obj.items():
                    if isinstance(v, str):
                        pairs.append('"%s": "%s"' % (k, v))
                    else:
                        pairs.append('"%s": %s' % (k, str(v)))
                return "{" + ", ".join(pairs) + "}"
            elif isinstance(obj, list):
                return "[" + ", ".join([self.format_json(x) for x in obj]) + "]"
            else:
                return str(obj)

    def write_response(self, response):
        try:
            # Python 3
            self.wfile.write(response.encode('utf-8'))
        except AttributeError:
            # Python 1.5.2
            self.wfile.write(response)

    def generate_journeys(self, origin, destination, out_datetime, ret_datetime):
        journeys = []

        # Helper to format datetime
        def format_datetime(year, month, day, hour, minute):
            return "%04d-%02d-%02dT%02d:%02d" % (year, month, day, hour, minute)

        # Generate outbound journeys
        year, month, day, hour, minute = out_datetime
        for offset in [-60, -30, 0, 30, 60]:
            # Calculate journey times
            adj_minutes = minute + offset
            adj_hour = hour + (adj_minutes // 60)
            adj_minute = adj_minutes % 60

            # Simple handling of day rollover
            adj_day = day + (adj_hour // 24)
            adj_hour = adj_hour % 24

            # Journey takes 1-2 hours
            duration = 60 + random.randint(0, 60)
            arr_hour = (adj_hour + (duration // 60))
            arr_minute = (adj_minute + (duration % 60)) % 60
            arr_day = adj_day + (arr_hour // 24)
            arr_hour = arr_hour % 24

            journey = {
                "id": "T%d" % random.randint(1000, 9999),
                "type": "outbound",
                "departure": origin,
                "arrival": destination,
                "departure_time": format_datetime(year, month, adj_day, adj_hour, adj_minute),
                "arrival_time": format_datetime(year, month, arr_day, arr_hour, arr_minute),
                "platform": str(random.randint(1, 8)),
                "price": round(30 + random.random() * 50, 2)
            }
            journeys.append(journey)

        # Generate return journeys if return datetime provided
        if ret_datetime[0] is not None:
            year, month, day, hour, minute = ret_datetime
            for offset in [-60, -30, 0, 30, 60]:
                adj_minutes = minute + offset
                adj_hour = hour + (adj_minutes // 60)
                adj_minute = adj_minutes % 60

                adj_day = day + (adj_hour // 24)
                adj_hour = adj_hour % 24

                duration = 60 + random.randint(0, 60)
                arr_hour = (adj_hour + (duration // 60))
                arr_minute = (adj_minute + (duration % 60)) % 60
                arr_day = adj_day + (arr_hour // 24)
                arr_hour = arr_hour % 24

                journey = {
                    "id": "T%d" % random.randint(1000, 9999),
                    "type": "return",
                    "departure": destination,
                    "arrival": origin,
                    "departure_time": format_datetime(year, month, adj_day, adj_hour, adj_minute),
                    "arrival_time": format_datetime(year, month, arr_day, arr_hour, arr_minute),
                    "platform": str(random.randint(1, 8)),
                    "price": round(30 + random.random() * 50, 2)
                }
                journeys.append(journey)

        return journeys

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == '/api/journeys':
            try:
                params = parse_qs(parsed_url.query)
                origin = params.get('from', [''])[0]
                destination = params.get('to', [''])[0]
                outbound_datetime = params.get('outbound_time', [''])[0]
                return_datetime = params.get('return_time', [''])[0]

                if not origin or not destination or not outbound_datetime:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.write_response(self.format_json({
                        "error": "Required parameters: 'from', 'to', and 'outbound_time'"
                    }))
                    return

                # Parse datetimes
                out_dt = parse_datetime(outbound_datetime)
                ret_dt = parse_datetime(return_datetime) if return_datetime else (
                    None, None, None, None, None)

                if out_dt[0] is None:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.write_response(self.format_json({
                        "error": "Invalid datetime format. Use YYYY-MM-DDTHH:MM"
                    }))
                    return

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                journeys = self.generate_journeys(
                    origin, destination, out_dt, ret_dt)
                response = self.format_json({"journeys": journeys})
                self.write_response(response)

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.write_response(self.format_json({"error": str(e)}))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path.startswith('/api/book/'):
            journey_id = parsed_url.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            booking_ref = "BR" + \
                "".join([random.choice(string.digits) for _ in range(5)])

            response = self.format_json({
                "booking_reference": booking_ref,
                "journey_id": journey_id,
                "status": "confirmed"
            })
            self.write_response(response)

        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    server = HTTPServer(('', 8080), TrainServer)
    print("Train booking server starting on port 8080...")
    server.serve_forever()


if __name__ == '__main__':
    run_server()
