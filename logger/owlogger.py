#!/usr/bin/env python3
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
import os

# for authentification
try:
    import jwt
    has_jwt = True
except:
    has_jwt = False
    
class MyServer(BaseHTTPRequestHandler):
    # class variables
    debug = False
    token = None
    db = None
    
    def do_GET(self):
                        
        # Respond to web request
        if self.debug:
            print(f"PATH <{self.path}>")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # test for file request
        # needed for js and css
        match self.path:
            case "/air-datepicker.css"|"/air-datepicker.js"|"/favicon.ico":
                with open(self.path.strip("/"),"rb") as f:
                    self.wfile.write(f.read())
                return

        # test URL
        if len(self.path) > 1:
            if self.path[1] != '?':
                return

        # parse url
        try:
            u = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        except:
            u = ({})

        if self.debug:
            print("GET ",u)

        # test for tokens (if specified)
        global tokens
        if tokens != None:
            # token list specified
            if "token" not in u:
                # token not sent
                return
            if u["token"][0] not in tokens:
                # token doesn't match
                if self.debug:
                    print("Non-matching token:",u["token"][0])
                return

        # parse url for date if present
        if "date" in u:
            # Date found
            date = u["date"][0]
        else:
            # Else use today
            date = datetime.date.today().isoformat()
            
        # check date
        try:
            daystart = datetime.datetime.fromisoformat(date)
        except:
            daystart = datetime.date.today()

        # Write page to browser
        self.wfile.write( bytes(self.make_html( daystart), "utf-8") )

    def do_POST(self):
        if self.token:
            # get token
            auth_header = self.headers.get('Authorization')
            if not auth_header or not authheader.startswith('Bearer'):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Token missing or incorrect")
                return
            # test token
            h_token = authheader.split(' ')[1]
            try:
                jwt.decode( h_token, token, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                self.send_response(401)
                self.wfile.write(b"Token missing or incorrect")
                self.end_headers()
                self.wfile.write(b"Token expired")
                return
            except jwt.InvalieTokenError:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Token invalid")
                return
        content_length = int(self.headers['Content-Length'])
        body_str = self.rfile.read(content_length)
        body = json.loads(body_str)
        self.send_response(200)
        self.end_headers()
#        print(body['data'])
        if self.debug:
            print("POST ",body)
        self.db.add( body['data'])

    def do_PUT(self):
        self.do_POST()

    def make_html( self, daystart ):
        # Get corresponding database entries for this date
        table_data = "".join(
            [ "<tr>"+"".join(["<td>"+c+"</td>" for c in row])+"</tr>"
                for row in self.db.day_data( daystart ) ]
            )
        if len(table_data)==0:
            table_data = "<tr><td colspan=2>&nbsp;&nbsp;No entries&nbsp;&nbsp;</td></tr>"

        # Get days with data
        dDays =  [ d[0] for d in self.db.distinct_days( daystart )]
        #print( "Distinct days", dDays )

        # Get months with data
        mDays =  [ f"{daystart.year}-{m[0]}-01" for m in self.db.distinct_months( daystart )]
        #print( "Distinct months", mDays )
        
        # Get years with data
        yDays =  [ f"{y[0]}-01-01" for y in self.db.distinct_years()]
        #print( "Distinct years", yDays )

        # Generate HTML
        return f"""
        <html>
            <head>
                <title>Logger</title>
                <style>
                    body {{overflow:hidden; font-size:2em;}}
                    #all {{width:100%; height:100%;display:flex;flex-direction:column; padding:10px; }}
                    #space {{display:flex; justify-content:space-between; flex-wrap:nowrap;}}
                    #crowd {{display:flex; align-items:center; flex-wrap:nowrap;}}
                    #uCal,input[type='text'] {{ font-size: 2em; }}
                    .present {{background-color: #e6ffe6;}}
                    #scroll {{overflow:scroll;}}
                    table {{ border-collapse: collapse;font-size:1em; }}
                    tr:nth-child(even) {{background-color: #D6EEEE; border-bottom: 1px solid #ddd; }}
                    td {{ padding-left: 1em; padding-right: 1em; }}
                </style>
                <link href="./air-datepicker.css" rel="stylesheet">
                <script src="./air-datepicker.js"></script>
            </head>
            <body>
                <div id='all'>
                    <div id="space"><span>owlogger</span><a href="#" onclick="globalThis.Today()">Today</a><a href="https://alfille.github.io/owlogger/" target="_blank" rel="noopener noreferrer">Help</a></div>
                    <div id="crowd"><button id='Ucal' onclick="globalThis.dp.show()"> &#128467;</button><input id='new_cal' type="text" size="10" readonly></div>                    
                    <hr>
                    <div id='scroll'>
                        <table>
                            <tr><th>Time</th><th>Data</th></tr>
                            {table_data}
                        </table>
                        <hr>
                        <a href="https://github.com/alfille/logger" target="_blank" rel="noopener noreferrer">Logger by Paul H Alfille 2025</a>
                    </div>
                </div>
            </body>
            <script>
                window.onload = () => {{
                    const d = new Date("{daystart}")
                    
                    goodDays={dDays};
                    goodMonths={mDays};
                    goodYears={yDays};

                    function TestDate(x) {{
                        switch (x.cellType) {{
                            case 'day':
                                return goodDays.includes(x.date.toISOString().split("T")[0]);
                            case 'month':
                                return goodMonths.includes(x.date.toISOString().split("T")[0]);
                            case 'year':
                                return goodYears.includes(x.date.toISOString().split("T")[0]);
                            default:
                                return false;
                            }}
                        }}

                    globalThis.dp = new AirDatepicker("#new_cal", {{
                            onSelect(x) {{NewDate(x.date)}},
                            isMobile:true,
                            selectedDates:[d],
                            onRenderCell(x) {{ if (TestDate(x)) {{ return {{classes:'present'}};}} }},
                        }} ) ;
                    }}
                function Today() {{ 
                    NewDate(new Date()); 
                    }} 
                function NewDate(date) {{
                    const d = date.toISOString().split("T")[0];
                    const url = new URL(location.href);
                    url.searchParams.set('date', d);

                    location.assign(url.search);
                    }}
            </script>
        </html>"""

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
        self.command(
            """CREATE INDEX IF NOT EXISTS idx_date ON datalog(date);"""
            )

    def add( self, value ):
        # Add a record
        if self.debug:
            print( f"Adding _{value}" )
        self.command( """INSERT INTO datalog( value ) VALUES (?) """, ( value, ) )

    def day_data( self, day ):
        # Get records from a full day
        nextday = day + datetime.timedelta(days=1)
        records = self.command( """SELECT TIME(date) as t, value FROM datalog WHERE DATE(date) BETWEEN DATE(?) AND DATE(?) ORDER BY t""", (day.isoformat(),nextday.isoformat()), True )
        #print(records)
        return records
        
    def distinct_days( self, day ):
        # get days with entries for range around day to inform the calendar
        firstday = day + datetime.timedelta(days=-34)
        lastday  = day + datetime.timedelta(days= 34)
        #print("range",firstday,lastday)
        records = self.command( """SELECT DISTINCT DATE(date) as d FROM datalog WHERE DATE(date) BETWEEN DATE(?) AND DATE(?) ORDER BY d""", (firstday.isoformat(),lastday.isoformat()), True )
        # returns singleton tuples with date 
        return records

    def distinct_months( self, day ):
        # get months with entries for this year to inform the calendar
        year = str(day.year)
        records = self.command( """SELECT DISTINCT strftime('%m', date) AS m FROM datalog WHERE strftime('%Y', date)=?  ORDER BY m""", (year,), True )
        # returns singleton tuples with text month number (2 digits)
        return records

    def distinct_years( self ):
        # get years with entries to inform the calendar
        records = self.command( """SELECT DISTINCT strftime('%Y', date) AS y FROM datalog ORDER BY y""", None, True )
        # returns singleton tuples with text year number (4 digits)
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
        #print("SQL ",records)
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
    parser.add_argument('-f','--file',
        required=False,
        default=dbfile,
        dest="dbfile",
        type=str,
        nargs='?',
        help=f'database file location (optional) default={dbfile}'
        )

    # secret token for JWT authentification
    parser.add_argument('-t','--token',
        required=False,
        default=argparse.SUPPRESS,
        dest="token",
        type=str,
        nargs='?',
        help='Optional authentification token (text string) to match with data source'
        )

    # Server address
    default_port = 8001
    server = f"localhost:{default_port}"
    parser.add_argument('-s','--server',
        required=False,
        default=server,
        dest="server",
        nargs='?',
        help=f'Server IP address and port (optional) default={server}'
        )
        
    # debug
    parser.add_argument( "-d", "--debug",
        required = False,
        default = False,
        dest="debug",
        action="store_true",
        help="Turn on some debugging output"
        )
        
    args=parser.parse_args()
    
    if args.debug:
        print("Debugging output on")
        print(sysargs,args)
        MyServer.debug = True

    #JWT token
    if "token" in args:
        if has_jwt:
            MyServer.token = args.token
        else:
            print("Error: token for JWT authentification supplied, but pyJWT not installed")
            print("Suggest apt install python3-jwt")
            sys.exit(2)
    else:
        MyServer.token=None

    # Handle server address
    if args.server.find('//')==-1:
        server = '//'.join(['http:',args.server])
    else:
        server = args.server
    print("server",server)
    
    u = urllib.parse.urlparse(server)
    print(u)
    port = u.port
    if port==None:
        port = default_port
        
    webServer = HTTPServer((u.hostname, port), MyServer)
    print("Server started %s:%s" % (u.hostname, port))

    MyServer.db = database(args.dbfile)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
 
if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
