#!/usr/bin/env python3
# owlogger_flask.py
#
# HTTP server program for logging data and serving pages
# Flask version of owlogger.py
# Uses owpost.py on data upload side
# Stores data in sqlite3
#
# by Paul H Alfille 2025 (Flask port)
# MIT License

import sqlite3
import argparse
import base64
import datetime
from io import BytesIO
import json
import sys
import tomllib
from urllib.parse import urlparse
from functools import wraps

# for Flask
try:
    from flask import Flask, request, Response, send_file, jsonify, g
except ImportError:
    print("Flask module needs to be installed")
    print("either 'pip install flask' or 'apt install python3-flask'")
    sys.exit(1)

# for Image
try:
    from PIL import Image, ImageDraw
except ImportError:
    print("PIL (Pillow) module needs to be installed")
    print("either 'pip install Pillow' or 'apt install python3-pil'")
    sys.exit(1)

# for authentication
try:
    import jwt
except ImportError:
    print("JWT module needs to be installed")
    print("either 'pip install PyJWT' or 'apt install python3-jwt'")
    sys.exit(1)

# for encryption
try:
    import bcrypt
except ImportError:
    print("bcrypt module needs to be installed")
    print("either 'pip install bcrypt' or 'apt install python3-bcrypt'")
    sys.exit(1)

app = Flask(__name__)

# --- Global config (set in main()) ---
debug = False
db = None
jwt_token = None
no_password = False


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _access_forbidden():
    """Return True if the request lacks valid Basic-Auth credentials."""
    if no_password:
        return False

    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        return True
    if not auth_header.lower().startswith("basic"):
        return True

    encoded_credentials = auth_header.split(' ')[1]
    try:
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
    except  ExpiredSignatureError:
        print("Token has expired!")    
    except (ValueError, UnicodeDecodeError) as e:
        print(f"Error decoding credentials: {e}")
        return True

    results = db.get_password(username)
    if len(results) != 1:
        return True

    if bcrypt.checkpw(password.encode('utf-8'), results[0][0].encode('utf-8')):
        return False

    return True


def _auth_challenge():
    """Return a 401 Basic-Auth challenge response."""
    print("Sending authentication challenge (401 Unauthorized)...")
    return Response(
        '<h1>Authentication Required</h1><p>Please provide valid credentials.</p>',
        status=401,
        headers={
            'WWW-Authenticate': 'Basic realm="Restricted area"',
            'Content-Type': 'text/html',
            'X-Frame-Options': 'SAMEORIGIN',
            'Cross-Origin-Opener-Policy': 'same-origin',
        }
    )


def require_basic_auth(f):
    """Decorator: enforce Basic-Auth on view functions."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if _access_forbidden():
            return _auth_challenge()
        return f(*args, **kwargs)
    return decorated


def _extract_bearer_token(auth_header):
    """
    Parse a Bearer token from an Authorization header string.
    Returns (token, error_message):
      - (token_str, None)  on success
      - (None, message)    on any malformed input
    Handles: missing header, wrong scheme, missing token,
             extra whitespace, and multi-part garbage.
    """
    if not auth_header:
        return None, "Authorization header missing"

    parts = auth_header.split()

    if len(parts) == 0:
        return None, "Authorization header is empty"

    if parts[0].lower() != 'bearer':
        return None, f"Unsupported auth scheme '{parts[0]}'; expected Bearer"

    if len(parts) == 1:
        return None, "Bearer token missing after scheme"

    if len(parts) > 2:
        return None, "Malformed Authorization header: unexpected extra fields"

    token = parts[1]
    if not token:
        return None, "Bearer token is empty"

    return token, None


def require_jwt(f):
    """Decorator: enforce JWT Bearer token on POST/PUT endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if jwt_token:
            auth_header = request.headers.get('Authorization')
            h_token, err = _extract_bearer_token(auth_header)
            if err:
                return Response(err, status=401)
            try:
                jwt.decode(h_token, jwt_token, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return Response("Token expired", status=401)
            except jwt.InvalidTokenError:
                return Response("Token invalid", status=401)
        return f(*args, **kwargs)
    return decorated


def best_practice_headers(response):
    """Add security headers to a response."""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    return response


# ---------------------------------------------------------------------------
# Static file routes (JS / CSS)
# ---------------------------------------------------------------------------

ALLOWED_FILES = {
    'air-datepicker.js':  'text/javascript',
    'owlogger.js':        'text/javascript',
    'air-datepicker.css': 'text/css',
    'owlogger.css':       'text/css',
}


@app.route('/<path:filename>')
def serve_static(filename):
    if filename not in ALLOWED_FILES:
        return Response(f'<h1>404 Not Found</h1><p>{filename}</p>', status=404, content_type='text/html')

    mime = ALLOWED_FILES[filename]
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return Response(f'File not found: {filename}', status=404)

    resp = Response(data, status=200, content_type=mime)
    resp.headers['Cache-Control'] = 'max-age=31536000'
    return best_practice_headers(resp)


# ---------------------------------------------------------------------------
# Frame-buffer / PNG routes
# ---------------------------------------------------------------------------

def _create_image(width=800, height=480):
    white, black = 1, 0
    img = Image.new('1', (width, height), color=white)
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 780, 460], outline=0, width=5)
    draw.text((350, 230), "REMOTE DASHBOARD", fill=black)
    return img


@app.route('/7in5')
@require_basic_auth
def frame_buffer():
    img = _create_image(800, 480)
    raw_buffer = img.tobytes()
    resp = Response(
        raw_buffer,
        status=200,
        content_type='application/octet-stream',
        headers={'Content-Length': str(len(raw_buffer))}
    )
    print(f"Sent {len(raw_buffer)} bytes")
    return best_practice_headers(resp)


@app.route('/test')
def frame_png():
    img = _create_image(800, 480)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    resp = send_file(buf, mimetype='image/png')
    print(f"Sent PNG")
    return best_practice_headers(resp)


# ---------------------------------------------------------------------------
# Main page (GET /)
# ---------------------------------------------------------------------------

@app.route('/')
@require_basic_auth
def index():
    # Parse query parameters
    date_str = request.args.get('date', datetime.date.today().isoformat())
    page_type_raw = request.args.get('type', 'data')

    type_map = {'week': 'week', 'plot': 'plot', 'stat': 'stat'}
    page_type = type_map.get(page_type_raw, 'data')

    try:
        daystart = datetime.datetime.fromisoformat(date_str)
    except ValueError:
        daystart = datetime.datetime.combine(datetime.date.today(), datetime.time())

    if debug:
        print(f"GET / date={date_str} type={page_type}")

    html = _make_html(daystart, page_type)
    resp = Response(html, status=200, content_type='text/html')
    return best_practice_headers(resp)


def _make_html(daystart, page_type):
    if page_type == 'week':
        dData = json.dumps(db.week_data(daystart))
    else:
        dData = json.dumps(db.day_data(daystart))

    dDays  = [d[0] for d in db.distinct_days(daystart)]
    mDays  = [f"{daystart.year}-{m[0]}-01" for m in db.distinct_months(daystart)]
    yDays  = [f"{y[0]}-01-01" for y in db.distinct_years()]

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
                <a class="button" id="data"  href="#" onclick="JumpTo.type('data')">Data</a>
                <a class="button" id="stat"  href="#" onclick="JumpTo.type('stat')">Stats</a>
                <a class="button" id="plot"  href="#" onclick="JumpTo.type('plot')">Graph</a>
                <a class="button" id="week"  href="#" onclick="JumpTo.type('week')">Week</a>
                <span id="date"></span>
                <span id="time"></span>
            </div>
            <div id="datebar" onclick="globalThis.dp.show()">
                <button id='Ucal'>&#128467;</button>
                <input id='new_cal' type="text" size="10" readonly hidden>&nbsp;<span id="showdate"></span>
            </div>
            <div id='contentarea'>
                <div class="non-plot">
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
            dayData:     JSON.parse('{dData}'),
            goodDays:    {dDays},
            goodMonths:  {mDays},
            goodYears:   {yDays},
            daystart:    new Date("{daystart}"),
            page_type:   "{page_type}",
            header_date: "{datetime.datetime.now().strftime("%m/%d/%Y")}",
            header_time: "{datetime.datetime.now().strftime("%H:%M")}",
        }};
    </script>
</html>"""


# ---------------------------------------------------------------------------
# Data ingestion (POST / PUT)
# ---------------------------------------------------------------------------

@app.route('/', methods=['POST', 'PUT'])
@require_jwt
def receive_data():
    body = request.get_json(force=True)
    if debug:
        print("POST", body)
    db.add(body['name'], body['data'])
    resp = Response('', status=200, content_type='text/html')
    return best_practice_headers(resp)


# ---------------------------------------------------------------------------
# Database class (unchanged from original)
# ---------------------------------------------------------------------------

class Database:
    def __init__(self, database="./logger_data.db"):
        self.database = database
        self.command(
            """CREATE TABLE IF NOT EXISTS datalog (
                id INTEGER PRIMARY KEY,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT '',
                value TEXT
            );""")
        self.command(
            """CREATE INDEX IF NOT EXISTS idx_date ON datalog(date);""")
        self.command(
            """CREATE TABLE IF NOT EXISTS version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER DEFAULT 0
            );""")
        self.command(
            """CREATE TABLE IF NOT EXISTS userlist (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            );""")

    def get_version(self):
        try:
            records = self.command("""SELECT version FROM version WHERE id = 1""", None, True)
        except Exception:
            return 0
        if not records:
            return 0
        return records[0][0]

    def set_version(self, v):
        self.command(
            """INSERT INTO version(id, version) VALUES (1, ?)
               ON CONFLICT(id) DO UPDATE SET version = excluded.version;""",
            (v,), False)

    def set_password(self, username, password_hash):
        self.command(
            """INSERT INTO userlist(username, password_hash) VALUES (?, ?)
               ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash;""",
            (username, password_hash), False)

    def add(self, source, value):
        if debug:
            print(f"Adding _{value}")
        # Fix #4: let SQLite set the timestamp in UTC via CURRENT_TIMESTAMP
        # rather than passing a Python local-time string.
        self.command(
            """INSERT INTO datalog(source, value) VALUES (?,?)""",
            (source, value))

    def day_data(self, day):
        nextday = day + datetime.timedelta(days=1)
        return self.command(
            """SELECT TIME(date) as t, source, value FROM datalog
               WHERE DATE(date) BETWEEN DATE(?) AND DATE(?) ORDER BY t""",
            (day.isoformat(), nextday.isoformat()), True)

    def week_data(self, day):
        nextday  = day + datetime.timedelta(days=1)
        firstday = day + datetime.timedelta(days=-6)
        records = self.command(
            """SELECT strftime('%J',date)-strftime("%J",?) as t, source, value
               FROM datalog
               WHERE DATE(date) BETWEEN DATE(?) AND DATE(?) ORDER BY t""",
            (firstday.isoformat(), firstday.isoformat(), nextday.isoformat()), True)
        if debug:  # Fix #6: was unconditional print()
            print(records)
        return records

    def distinct_days(self, day):
        firstday = day + datetime.timedelta(days=-34)
        lastday  = day + datetime.timedelta(days= 34)
        return self.command(
            """SELECT DISTINCT DATE(date) as d FROM datalog
               WHERE DATE(date) BETWEEN DATE(?) AND DATE(?) ORDER BY d""",
            (firstday.isoformat(), lastday.isoformat()), True)

    def distinct_months(self, day):
        # Fix #5: use a range comparison so idx_date can be used.
        # strftime('%Y', date) = ? applies a function to every row,
        # preventing index use entirely.
        year_start = f"{day.year}-01-01"
        year_end   = f"{day.year + 1}-01-01"
        return self.command(
            """SELECT DISTINCT strftime('%m', date) AS m FROM datalog
               WHERE date >= ? AND date < ? ORDER BY m""",
            (year_start, year_end), True)

    def distinct_years(self):
        return self.command(
            """SELECT DISTINCT strftime('%Y', date) AS y FROM datalog ORDER BY y""",
            None, True)

    def get_password(self, username):
        return self.command(
            """SELECT password_hash FROM userlist WHERE username=?""",
            (username,), True)

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def command(self, cmd, value_tuple=None, fetch=False):
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                # Fix #3: guard with `is not None` so empty tuple () is not skipped
                if value_tuple is not None:
                    cursor.execute(cmd, value_tuple)
                else:
                    cursor.execute(cmd)
                # Fix #1: fetchall() called inside the `with` block before
                # the connection closes.
                if fetch:
                    records = cursor.fetchall()
                else:
                    records = None
                    conn.commit()
        except sqlite3.Error as e:
            # Fix #7: was only catching OperationalError; now catches all
            # SQLite errors (IntegrityError, ProgrammingError, etc.)
            print(f"Database error <{self.database}>: {e}")
            raise
        return records


# ---------------------------------------------------------------------------
# Password utility
# ---------------------------------------------------------------------------

def set_password(database, username, password):
    database.set_password(
        username,
        bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))


# ---------------------------------------------------------------------------
# Config helpers (unchanged logic)
# ---------------------------------------------------------------------------

def read_toml(args):
    if hasattr(args, 'config') and args.config:
        try:
            with open(args.config, "rb") as c:
                return tomllib.load(c)
        except tomllib.TOMLDecodeError as e:
            with open(args.config, "rb") as c:
                contents = c.read()
            for i, line in enumerate(contents.decode('utf-8').split("\n"), 1):
                print(f"{i:3d}. {line}")
            print(f"Trouble reading configuration file {args.config}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Cannot open TOML configuration file: {args.config}")
    return {}


def address_tuple(address_string, default_port):
    u = urlparse(address_string)
    if not u.scheme:                       # correct: detect missing scheme via attribute
        u = urlparse(f"http://{address_string}")
    port = u.port or default_port
    host = u.hostname or "localhost"       # urlparse splits host/port cleanly; safe for IPv6
    return host, port


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(sysargs):
    global debug, db, jwt_token, no_password

    # Pass 1: find --config
    pre_parser = argparse.ArgumentParser(add_help=False)
    default_config = "/etc/owlogger/owlogger.toml"
    pre_parser.add_argument("-c", "--config",
        required=False, default=default_config,
        dest="config", type=str, nargs="?",
        help=f"Location of any configuration file. Optional default={default_config}")
    pre_args, remaining_argv = pre_parser.parse_known_args()

    toml = read_toml(pre_args)

    # Pass 2: full argument set
    parser = argparse.ArgumentParser(
        parents=[pre_parser],
        prog="owlogger_flask",
        description="Logs 1-wire data to a database that can be viewed on the web. Flask edition.",
        epilog="Repository: https://github.com/alfille/owlogger")

    default_port = 8001
    default_address = f"localhost:{default_port}"
    parser.add_argument('-a', '--address',
        required=False, default=toml.get("address", default_address),
        dest="address", nargs='?', type=str,
        help=f'Server IP address and port (optional) default={default_address}')

    parser.add_argument('-t', '--token',
        required=False, default=toml.get("token", argparse.SUPPRESS),
        dest="token", type=str, nargs='?',
        help='Optional JWT secret token to match with owpost/generalpost.')

    dbfile = "./logger_data.db"
    parser.add_argument('-f', '--file',
        required=False, default=toml.get("database", dbfile),
        dest="database", type=str, nargs='?',
        help=f'Database file location (optional) default={dbfile}')

    parser.add_argument("-d", "--debug",
        required=False, default=toml.get("debug", False),
        dest="debug", action="store_true",
        help="Print debugging information")

    parser.add_argument("--no_password",
        required=False, default=toml.get("no_password", False),
        dest="no_password", action="store_true",
        help="Turns off password protection")

    args = parser.parse_args(remaining_argv)

    debug = args.debug
    if debug:
        print("Debugging output on")
        print(sysargs, args)

    jwt_token = getattr(args, 'token', None)
    no_password = args.no_password

    addr, port = address_tuple(args.address, default_port)
    db = Database(args.database)

    print(f"Server started {addr}:{port}")
    # Use Flask's built-in dev server; swap for gunicorn/waitress in production:
    #   gunicorn -b addr:port owlogger_flask:app
    app.run(host=addr, port=port, debug=debug)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
else:
    print("Standalone program — import as WSGI app via `app`")
