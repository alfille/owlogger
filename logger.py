# logger.py
#
# HTTP server program for logging data and serving pages
# Uses putter.py on data upload side
# Stores data in sqlite3
#
# by Paul H Alfille 2025
# MIT License

import sqlite3

# Strategy
# Database
#  Open if exists
#  Else create
# Table format:
#  Time = datatime
#  Data = text

# Wait for put input
# Add to database


from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import datetime
import urllib
from urllib.parse import urlparse
import json

hostName = "localhost"
serverPort = 8001

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        print("GET GET GET")
        # Respond to web request
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # parse url for date if present
        print("parsing")
        try:
            d = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        except:
            d = ({})
        print(urllib.parse.urlparse(self.path))
        print(urllib.parse.urlparse(self.path).query)
        print(d)

        if "date" in d:
            date = d["date"][0]
            print("found", date )
        else:
            date = datetime.date.today().isoformat()
            print("not found", date )

        # Get corresponding database entries for this date
        global db
        table_data = "".join(
            [ "<tr>"+"".join(["<td>"+c+"</td>" for c in row])+"</tr>"
                for row in db.day_data( datetime.datetime.fromisoformat(date) ) ]
            )
        print("table_data",table_data)

        # Generate HTML
        html = f"""
        <html>
            <head>
                <title>Logger</title>
                <style>
                    table {{ border-collapse: collapse; }}
                    tr:nth-child(even) {{background-color: #D6EEEE; border-bottom: 1px solid #ddd; }}
                    td {{ padding-left: 1em; padding-right: 1em; }}
                    body {{overflow:hidden; }}
                    .top {{font-size:2em; }}
                    .scroll {{overflow:scroll;height:100%;}}
                </style>
            </head>
            <body onload=SetDate('{date}')>
                <div class='top'>
                    <input type='date' id='date_pick' oninput='NewDate()'>&nbsp;&nbsp;{date}
                    <br>
                </div>
                <div class='scroll'>
                    <table>
                        <tr><th>Time</th><th>Data</th></tr>
                        {table_data}
                    </table>
                </div>
            </body>
            <script>
                function SetDate(date) {{
                    let d
                    try {{
                        d = new Date(date)
                        if ( isNaN(d) ) {{
                            d = new Date()
                        }}
                    }}
                    catch {{
                        d = new Date()
                    }}
                    document.getElementById('date_pick').value = d.toISOString().split("T")[0]
                }}
                function NewDate() {{
                    const newdate = document.getElementById('date_pick').value
                    const url = new URL(location.href);
                    url.searchParams.set('date', newdate);

                    location.assign(url.search);
                }}
            </script>
        </html>"""

        # Write page to browser
        self.wfile.write(bytes(html, "utf-8"))

    def do_POST(self):
        # From putter.py
        content_length = int(self.headers['Content-Length'])
        body_str = self.rfile.read(content_length)
        body = json.loads(body_str)
        self.send_response(200)
        self.end_headers()
#        response = BytesIO()
#        response.write(b'This is POST request. ')
#        response.write(b'Received: ')
#        response.write(body_str)
#        self.wfile.write(response.getvalue())
#        print(body['data'])
        global db
        db.add( body['data'])

    def do_PUT(self):
        self.do_POST()

class database:
    # sqlite3 interface
    def __init__(self, database="./logger_data.db"):
        # Create database if needed
        self.database = database
        self.command(
            """CREATE TABLE IF NOT EXISTS datalog (
                id INTEGER PRIMARY KEY, 
                date DATATIME DEFAULT CURRENT_TIMESTAMP, 
                value TEXT
            );""" )

    def add( self, value ):
        # Add a record
        print( f"Adding _{value}" )
        self.command( """INSERT INTO datalog( value ) VALUES (?) """, ( value, ) )

    def day_data( self, day ):
        # Get records from a full day
        nextday = day + datetime.timedelta(days=1)
        records = self.command( """SELECT time(date),value FROM datalog WHERE date BETWEEN date(?) AND date(?) ORDER BY date""", (day.isoformat(),nextday.isoformat()), True )
        print(records)
        return records

    def command( self, cmd, value_tuple=None, fetch=False ):
        # Connect to database and handle command
        print(cmd)
        print(value_tuple)
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                if value_tuple:
                    cursor.execute( cmd, value_tuple )
                else:
                    cursor.execute( cmd )
            if fetch:
                records = cursor.fetchall()
            else:
                records = None
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Failed to open database <{self.database}>:", e)
            raise e
        return records

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    global db
    db = database()
    db.day_data( datetime.date.today() )

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
 
