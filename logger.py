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
import sys
import datetime
import argparse
import urllib
from urllib.parse import urlparse
import json

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        # Respond to web request
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # test URL
        if len(self.path) > 1:
            if self.path[1] != '?':
                return

        # parse url
        try:
            u = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        except:
            u = ({})

        # test for tokens (if specified)
        global tokens
        if tokens != None:
            # token list specified
            if "token" not in u:
                # token not sent
                return
            if u["token"][0] not in tokens:
                # token doesn't match
                return

        # parse url for date if present
        if "date" in u:
            # Date found
            date = u["date"][0]
            #print("found", date )
        else:
            # Else use today
            date = datetime.date.today().isoformat()
            #print("not found", date )

        # Get corresponding database entries for this date
        global db
        table_data = "".join(
            [ "<tr>"+"".join(["<td>"+c+"</td>" for c in row])+"</tr>"
                for row in db.day_data( datetime.datetime.fromisoformat(date) ) ]
            )
        if len(table_data)==0:
            table_data = "<tr><td colspan=2>&nbsp;&nbsp;No entries&nbsp;&nbsp;</td></tr>"

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
                    <hr>
                </div>
                <div class='scroll'>
                    <table>
                        <tr><th>Time</th><th>Data</th></tr>
                        {table_data}
                    </table>
                    <hr>
                    <a href="https://github.com/alfille/logger">Logger by Paul H Alfille 2025</a>
                </div>
            </body>
            <script>
                function SetDate(date) {{
                    //console.log("SetDate",date)
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
                    //console.log("NewDate",newdate)
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
        #print( f"Adding _{value}" )
        self.command( """INSERT INTO datalog( value ) VALUES (?) """, ( value, ) )

    def day_data( self, day ):
        # Get records from a full day
        nextday = day + datetime.timedelta(days=1)
        records = self.command( """SELECT time(date),value FROM datalog WHERE date BETWEEN date(?) AND date(?) ORDER BY date""", (day.isoformat(),nextday.isoformat()), True )
        #print(records)
        return records

    def command( self, cmd, value_tuple=None, fetch=False ):
        # Connect to database and handle command
        #print(cmd)
        #print(value_tuple)
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

def main(sysargs):
    dbfile = "./logger_data.db"
    # Command line first
    parser = argparse.ArgumentParser(
        prog="1-wire Logger",
        description="Log 1-wire data externally to protect interior environment\nLogger and webserver component",
        epilog="Repository: https://github.com/alfille/logger")

    # Database file
    dbfile = "logger_data.db"
    parser.add_argument('-d','--dbfile',
        metavar="DB_FILE",
        required=False,
        default=dbfile,
        dest="dbfile",
        type=str,
        nargs='?',
        help=f'database file location (optional) default={dbfile}'
        )

    # token list
    parser.add_argument('-t','--tokens',
        metavar="TOKEN",
        required=False,
        default=argparse.SUPPRESS,
        dest="tokens",
        type=str,
        nargs='*',
        help='Token list to accept from putter.py (optonal)'
        )

    # Server address
    address = "localhost"    
    parser.add_argument('-a','--address',
        required=False,
        metavar="IP_ADDRESS",
        default=address,
        dest="address",
        nargs='?',
        help=f'Server IP address (optional) default={address}'
        )

    # Server port    
    port = 8001
    parser.add_argument('-p','--port',
        metavar="PORT",
        required=False,
        default=port,
        dest="port",
        type=int,
        nargs='?',
        help=f'Server port (optional) default={port}'
        )    
        
    args=parser.parse_args()
    print(sysargs,args)

    
    webServer = HTTPServer((args.address, args.port), MyServer)
    print("Server started http://%s:%s" % (args.address, args.port))

    global tokens
    if "tokens" in args:
        tokens = args.tokens
    else:
        tokens = None

    global db
    db = database(args.dbfile)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
 
if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
