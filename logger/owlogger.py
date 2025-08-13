#!/usr/bin/env python3
# owlogger.py
#
# HTTP server program for logging data and serving pages
# Uses owpost.py on data upload side
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
    token = None
    db = None
    no_password = False
    
    def do_GET(self):
        global debug
                        
        # Respond to web request
        if debug:
            print(f"PATH <{self.path}>")

        # test for file request
        # needed for js and css
        match self.path:
            # check for permitted file requests (only a few carefully chosen)
            case  "/air-datepicker.js"  \
                | "/owlogger.js"        \
                : return self.file_return("text/html")
            case  "/air-datepicker.css" \
                | "/owlogger.css"       \
                : return self.file_return("text/css")
            case  "/owlogger.css"       \
                : return self.file_return("image/x-icon") 

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

        if debug:
            print("GET ",u)

        # parse url for date if present
        if "date" in u:
            # Date found
            date = u["date"][0]
        else:
            # Else use today
            date = datetime.date.today().isoformat()
            
        # parse url for type if present
        if "type" in u:
            match u["type"][0]:
                case "plot":
                    self.type = "plot"
                case "stat":
                    self.type = "stat"
                case _:
                    self.type = "data"
        else:
            self.type = "data"
            
        # check date
        try:
            daystart = datetime.datetime.fromisoformat(date)
        except:
            daystart = datetime.date.today()

        # Write page to browser
        self.wfile.write( bytes(self._make_html( daystart), "utf-8") )

    def do_POST(self):
        global debug
        
        # Is JWT enabled in owlogger? (enabled by token in command line)
        if self.token:
            # get token
            #print("self.headers",self.headers)
            auth_header = self.headers.get('Authorization')
            #print("auth_header",auth_header)
            if not auth_header or not auth_header.startswith('Bearer'):
                return self._bad_post("Token missing")
            # test token
            h_token = auth_header.split(' ')[1]
            try:
                jwt.decode( h_token, self.token, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return self._bad_post("Token expired")
            except jwt.InvalidTokenError:
                return self._bad_post( "Token invalid")

        content_length = int(self.headers['Content-Length'])
        body_str = self.rfile.read(content_length)
        body = json.loads(body_str)
        self._good_get()
        if debug:
            print("POST ",body)
        self.db.add( body['name'], body['data'] )
        
    def _bad_post( self, message ):
        global debug
        
        self.send_response(401)
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
        if debug:
            print(message)
            
    def _good_get( self ):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.best_practice()

    def file_return( self, ftype ):
        self.send_response(200)
        self.send_header("Content-type", ftype)
        self.send_header("Cache-Control", "max-age=31536000")
        self.best_practice()
        with open(self.path.strip("/"),"rb") as f:
            self.wfile.write(f.read())

    def best_practice( self ):
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.end_headers()

    def do_PUT(self):
        self.do_POST()

    def _make_html( self, daystart ):
        # Get corresponding database entries for this date
        dData = json.dumps(self.db.day_data( daystart ))

        # Get days with data
        dDays =  [ d[0] for d in self.db.distinct_days( daystart )]

        # Get months with data
        mDays =  [ f"{daystart.year}-{m[0]}-01" for m in self.db.distinct_months( daystart )]
        
        # Get years with data
        yDays =  [ f"{y[0]}-01-01" for y in self.db.distinct_years()]

        # Generate HTML
        return f"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>OWLogger</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Display 1-wire sensor readings logged to a cloud server.">
        <link rel="stylesheet" href="./owlogger.css" type="text/css">
        <script src="./owlogger.js"></script>
        <link href="./air-datepicker.css" rel="stylesheet" type="text/css" defer>
        <script src="./air-datepicker.js" defer></script>
    </head>
    <body>
        <div id='all'>
            <div id="toolbar">
                <a class="button" id="reload" href="https://alfille.github.io/owlogger/" target="_blank" rel="noopener noreferrer">OWLogger</a>
                <a class="button" id="data" href="#" onclick="JumpTo.type('data')">Data</a>
                <a class="button" id="stat" href="#" onclick="JumpTo.type('stat')">Stats</a>
                <a class="button" id="plot" href="#" onclick="JumpTo.type('plot')">Graph</a>
                <span id="date"></span>
                <span id="time"></span>
            </div>
            <div id="datebar" onclick="globalThis.dp.show()">
                <button id='Ucal'>&#128467;</button>
                <input id='new_cal' type="text" size="10" readonly hidden>&nbsp;<span id="showdate"></span>
            </div>                    
            <div id='contentarea'>
                <div  class="non-plot">
                    <table id="table"></table>
                </div>
                <div id="graph" class="yes-plot">
                    <canvas id="graphcanvas"></canvas>
                </div>
            </div>
            <div id="footer">
                <div class="non-plot">
                     <a id="bfooter" class="button" href="https://github.com/alfille/owlogger" target="_blank" rel="noopener noreferrer">OWLogger by Paul H Alfille 2025</a>
                </div>
                <div class="yes-plot">
                    <div id="legend"></div>
                </div>
           </div>
        </div>
    </body>
    <script>
        var globals = {{
            dayData: JSON.parse('{dData}'),
            goodDays: {dDays},
            goodMonths: {mDays},
            goodYears:{yDays},
            daystart: new Date("{daystart}"),
            page_type: "{self.type}",
            header_date:"{datetime.datetime.now().strftime("%m/%d/%Y")}",
            header_time:"{datetime.datetime.now().strftime("%H:%M")}",
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
                source TEXT DEFAULT '',
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

    def add( self, source, value ):
        global debug
        
        # Add a record
        if debug:
            print( f"Adding _{value}" )
        self.command( """INSERT INTO datalog( date, source, value ) VALUES (?,?,?) """, 
            ( datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), source, value, ) 
            )

    def day_data( self, day ):
        # Get records from a full day
        nextday = day + datetime.timedelta(days=1)
        records = self.command( """SELECT TIME(date) as t, source, value FROM datalog WHERE DATE(date) BETWEEN DATE(?) AND DATE(?) ORDER BY t""", (day.isoformat(),nextday.isoformat()), True )
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
        
# for setting password -- separate program flow
def set_password( db, username, password ):
    db.set_password( username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') )
    
def read_toml( args ):
    if "config" in args:
        try:
            with open( args.config, "rb" ) as c:
                toml = tomllib.load(c)
        except tomllib.TOMLDecodeError as e:
            with open ( args.config, "rb" ) as c:
                contents = c.read()
            for lin in zip(range(1,200),contents.decode('utf-8').split("\n")):
                print(f"{lin[0]:3d}. {lin[1]}")
            print(f"Trouble reading configuration file {args.config}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config}")
            toml={}
    return toml

def address_tuple( address_string, default_port ):
    # takes a server string in a variety of formats and returns the bare needed components
    
    # Handle server address
    address = address_string
    
    # Add http:// for url processing even though it's not poart of the final result
    if address.find("//") == -1:
        address = f"http://{address}"
    
    # url parse and extract port
    u = urllib.parse.urlparse(address)
    port = u.port
    if port==None:
        port = default_port
        
    # netloc can include port, so remove 
    netloc = u.netloc.split(':')[0]
    
    return netloc, port

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
    toml = read_toml( args )

    # Second pass at command line
    parser = argparse.ArgumentParser(
        parents=[parser],
        prog="owlogger",
        description="Logs 1-wire data to a database that can be viewed on the web. Works with 'owpost' and 'generalpost'",
        epilog="Repository: https://github.com/alfille/owlogger"
        )

    # Server address
    default_port = 8001
    address = f"localhost:{default_port}"
    parser.add_argument('-a','--address',
        required=False,
        default=toml.get("address",address),
        dest="address",
        nargs='?',
        type=str,
        help=f'Server IP address and port (optional) default={address}'
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
    
    global debug
    if args.debug:
        print("Debugging output on")
        print(sysargs,args)
        debug = True
    else:
        debug = False

    #JWT token
    if "token" in args:
        OWLogServer.token = args.token
    else:
        OWLogServer.token = None
        
    OWLogServer.no_password = args.no_password

    # Handle server address
    (addr,port) = address_tuple( args.address, default_port )
    try:
        webServer = HTTPServer((addr, port), OWLogServer)
    except OSError as e:
        print( f"Could not start web server at {addr}:{port} -- {e}" )
        sys.exit(1)
    print(f"Server started {addr}:{port}")

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
