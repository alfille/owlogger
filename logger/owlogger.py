#!/usr/bin/env python3
# owlogger.py
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

import argparse
import base64
import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import json
import sys
import tomllib
import urllib
from urllib.parse import urlparse

# for authentification
try:
    import jwt
except:
    print("JWT module needs to be installed")
    print("either 'pip install PyJWT' or 'apt install python3-jwt'")
    sys.exit(1)

# for encryption
try:
    import bcrypt
except:
    print("bcrypt module needs to be installed")
    print("either 'pip install bcrypt' or 'apt install python3-bcrypt'")
    sys.exit(1)
    
class OWLogServer(BaseHTTPRequestHandler):
    # class variables
    debug = False
    token = None
    db = None
    no_password = False
    
    def do_GET(self):
                        
        # Respond to web request
        if self.debug:
            print(f"PATH <{self.path}>")

        # test for file request
        # needed for js and css
        match self.path:
            # check for permitted file requests (only a few carefully chosen)
            case "/air-datepicker.css"|"/air-datepicker.js"|"/favicon.ico":
                with open(self.path.strip("/"),"rb") as f:
                    self._good_get()
                    self.wfile.write(f.read())
                return

        # test URL -- only queries allowed
        if len(self.path) > 1:
            if self.path[1] != '?':
                ## null response to random url
                self._good_get()
                return

        # test username and password
        if self._access_forbidden():
            return self._send_auth_challenge()
        
        # Good user, continue 
        self._good_get()

        # parse url
        try:
            u = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        except:
            u = ({})

        if self.debug:
            print("GET ",u)

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
        self.wfile.write( bytes(self._make_html( daystart), "utf-8") )

    def do_POST(self):
        # Is JWT enabled in owlogger? (enabled by token in command line)
        if self.token:
            # get token
            auth_header = self.headers.get('Authorization')
            if not auth_header or not authheader.startswith('Bearer'):
                return self._bad_post("Token missing")
            # test token
            h_token = authheader.split(' ')[1]
            try:
                jwt.decode( h_token, token, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return self._bad_post("Token expired")
            except jwt.InvalidTokenError:
                return self._bad_post( "Token invalid")
        content_length = int(self.headers['Content-Length'])
        body_str = self.rfile.read(content_length)
        body = json.loads(body_str)
#        self.send_response(200)
#        self.end_headers()
        self._good_get()
        if self.debug:
            print("POST ",body)
        self.db.add( body['data'])
        
    def _bad_post( self, message ):
        self.send_response(401)
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
        if self.debug:
            print(message)
            
    def _good_get( self ):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_PUT(self):
        self.do_POST()

    def _make_html( self, daystart ):
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
        
    def _send_auth_challenge(self):
        """Sends an HTTP 401 Unauthorized response with a Basic Auth challenge."""
        print("Sending authentication challenge (401 Unauthorized)...")
        self.send_response(401)
        self.send_header('WWW-Authenticate', f'Basic realm="Restricted area"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Authentication Required</h1><p>Please provide valid credentials.</p>')

    def _access_forbidden( self ):
        if self.no_password:
            return False # default good
        
        # Check header
        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            return True # bad
        if not auth_header.lower().startswith("basic"):
            return True # bad
        
        # Extract the base64 encoded part
        encoded_credentials = auth_header.split(' ')[1]
        
        try:
            # Decode from base64 and then from bytes to string
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error decoding credentials: {e}")
            return True # bad

        results = self.db.get_password( username )
        if len(results) != 1:
            return True # bad -- not in database
            
        if bcrypt.checkpw(password.encode('utf-8'), results[0][0].encode('utf-8') ):
            return False ; # password ok!
            
        return True # Bad 

class Database:
    # sqlite3 interface
    def __init__(self, database="./logger_data.db"):
        # Create database if needed
        self.database = database
        # log table
        self.command(
            """CREATE TABLE IF NOT EXISTS datalog (
                id INTEGER PRIMARY KEY, 
                date DATATIME DEFAULT CURRENT_TIMESTAMP, 
                value TEXT
            );""" )
        self.command(
            """CREATE INDEX IF NOT EXISTS idx_date ON datalog(date);"""
            )
        # version table (single record)
        self.command(
            """CREATE TABLE IF NOT EXISTS version (
                id INTEGER PRIMARY KEY CHECK (id = 1), 
                version INTEGER DEFAULT 0
            );""" )
        # user/password table
        self.command(
            """CREATE TABLE IF NOT EXISTS userlist (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            );""" )

    def get_version( self ):
        try:
            records = self.command( """SELECT version FROM version WHERE id = 1""", None, True )
        except:
            return 0
        if len(records)==0:
            return 0;
        return records[0][0]

    def set_version( self, v ):
        self.command( 
            """INSERT INTO version( id, version)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    version = excluded.version
                ;""", ( v, ), False )
        
    def set_password( self, username, password_hash ):
        self.command( 
            """INSERT INTO userlist( username, password_hash )
                VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash = excluded.password_hash
                ;""", ( username, password_hash ), False )

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

    def get_password( self, username ):
        # get password if exists
        records = self.command( """SELECT password_hash FROM userlist WHERE username=?""", (username,), True )
        # returns single element list or empty list
        return records

    def hash_password(self, password):
        """Hashes a plaintext password using bcrypt."""
        # bcrypt.hashpw expects bytes, so encode the password
        # bcrypt.gensalt() generates a random salt and appropriate cost factor
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
            print(f"Failed to open database <{self.database}>: {e}")
            raise e
        #print("SQL ",records)
        return records
        
# for setting password -- separat program flow
def set_password( db, username, password ):
    db.set_password( username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') )

def main(sysargs):
    
    # Look for a config file location (else default) 
    # read it in TOML format
    # allow command line parameters to over-rule
    
    # Step 1: Parse only the --config argument
    parser = argparse.ArgumentParser(
        add_help=False
        )
    
    config = "/etc/owlogger/owlogger.toml"
    # config
    parser.add_argument("--config",
        required=False,
        default=config,
        dest="config",
        type=str,
        nargs="?",
        help=f"Location of any configuration file. Optional default={config}"
        )
    args, remaining_argv = parser.parse_known_args()

    # Process TOML
    # TOML file
    if "config" in args:
        try:
            with open( initial_args.config, "rb" ) as c:
                contents = c.readlines()
                try:
                    toml=tomllib.loads(contents)
                except TOMLDecodeError as e:
                    for lin in zip(range(1,200),contents.split("\n")):
                        print(f"{lin[0]:3d}. {lin[1]}")
                    print(f"Trouble reading configuration file {args.config}: {e.msg}")
                    sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config}")
            toml={}


    # Second pass at command line
    parser = argparse.ArgumentParser(
        parents=[parser],
        prog="owlogger",
        description="Logs 1-wire data to a database that can be viewed on the web. Works with 'owpost' and 'generalpost'",
        epilog="Repository: https://github.com/alfille/owlogger"
        )

    # Server address
    default_port = 8001
    server = f"localhost:{default_port}"
    parser.add_argument('-s','--server',
        required=False,
        default=toml.get("server",server),
        dest="server",
        nargs='?',
        type=str,
        help=f'Server IP address and port (optional) default={server}'
        )
        
    # secret token for JWT authentification
    parser.add_argument('-t','--token',
        required=False,
        default=toml.get("token",argparse.SUPPRESS),
        dest="token",
        type=str,
        nargs='?',
        help='Optional authentification token (text string) to match with owpost or generalpost. JWT secret.'
        )

    # Database file
    dbfile = "./logger_data.db"
    parser.add_argument('-f','--file',
        required=False,
        default=toml.get("database",dbfile),
        dest="database",
        type=str,
        nargs='?',
        help=f'database file location (optional) default={dbfile}'
        )

    # debug
    parser.add_argument( "-d", "--debug",
        required = False,
        default = toml.get("debug",False),
        dest="debug",
        action="store_true",
        help="Print debugging information"
        )
        
    # no password
    parser.add_argument( "--no_password",
        required = False,
        default = toml.get("no_password",False),
        dest="no_password",
        action="store_true",
        help="Turns off password protection"
        )
        
    args=parser.parse_args(remaining_argv)
    print("args",args)
    
    # TOML file
    if "config" in args:
        try:
            with open( args.config, "rb" ) as c:
                try:
                    toml=tomllib.load(c)
                except TOMLDecodeError as e:
                    print(f"Trouble reading configuration file {args.config}: {e.msg}")
                    sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config}")
            toml={}
    
    if args.debug:
        print("Debugging output on")
        print(sysargs,args)
        OWLogServer.debug = True

    #JWT token
    OWLogServer.token = args.get("token",None)
        
    OWLogServer.no_password = args.no_password

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
        
    webServer = HTTPServer((u.hostname, port), OWLogServer)
    print("Server started %s:%s" % (u.hostname, port))

    OWLogServer.db = Database(args.database)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
 
if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program")
