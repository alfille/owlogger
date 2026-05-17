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
#
# ── Modes ────────────────────────────────────────────────────────────────────
#
#  Standalone (Flask dev server, direct TCP):
#    python owlogger_flask.py [options]
#
#  Production (gunicorn → UNIX socket ← Caddy reverse proxy):
#    gunicorn -c gunicorn.conf.py owlogger_flask:app
#    (managed by owlogger.service; Caddy configured in Caddyfile)
#
# ── Configuration priority (highest → lowest) ─────────────────────────────
#
#  Standalone:
#    CLI arguments  →  env vars  →  TOML file  →  built-in defaults
#
#  Gunicorn / systemd:
#    env vars (from systemd EnvironmentFile=)  →  TOML file  →  built-in defaults
#    (CLI arguments are unavailable; gunicorn owns sys.argv)
#
# ── Environment variables (set in /etc/owlogger/owlogger.env) ─────────────
#
#  OWLOGGER_CONFIG       path to a non-default TOML file
#  OWLOGGER_DATABASE     path to SQLite database file
#  OWLOGGER_TOKEN        JWT secret for POST/PUT endpoints
#  OWLOGGER_NO_PASSWORD  1 / true / yes  →  disable Basic-Auth
#  OWLOGGER_ADDRESS      host:port for standalone mode only
#
# ── TOML keys ─────────────────────────────────────────────────────────────
#
#  address, token, database, debug, no_password
#
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3
import argparse
import base64
import datetime
from io import BytesIO
import json
import os
import sys
import logging # forwarded to gunicorn
import tomllib
from urllib.parse import urlparse
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# for Flask
try:
    from flask import Flask, request, Response, send_file
except ImportError:
    logging.error("Flask module needs to be installed. Do 'pip install flask' or 'apt install python3-flask'")
    sys.exit(1)

# for Image
try:
    from PIL import Image, ImageDraw
except ImportError:
    logging.error("PIL (Pillow) module needs to be installed. Do 'pip install Pillow' or 'apt install python3-pil'")
    sys.exit(1)

# for authentication
try:
    import jwt
except ImportError:
    logging.error("JWT module needs to be installed. Do 'pip install PyJWT' or 'apt install python3-jwt'")
    sys.exit(1)

# for encryption
try:
    import bcrypt
except ImportError:
    logging.error("bcrypt module needs to be installed. Do 'pip install bcrypt' or 'apt install python3-bcrypt'")
    sys.exit(1)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Globals (set by init_app() before any request is served)
# ---------------------------------------------------------------------------
db          = None
jwt_token   = None
no_password = False

_DEFAULT_CONFIG  = "/etc/owlogger/owlogger.toml"
_DEFAULT_PORT    = 8001
_DEFAULT_ADDRESS = f"localhost:{_DEFAULT_PORT}"
_DEFAULT_DB      = "./logger_data.db"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _read_toml(config_path):
    """Load a TOML file; return {} if missing or path is None."""
    if not config_path:
        return {}
    try:
        with open(config_path, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        logging.info(f"No toml configuration file {config_path}")
        return {}
    except PermissionError:
        logging.error(f"Access to {config_path} denied.")
        sys.exit(1)
    except tomllib.TOMLDecodeError as e:
        with open(config_path, "rb") as fh:
            contents = fh.read()
        for i, line in enumerate(contents.decode("utf-8").split("\n"), 1):
            logging.info(f"{i:3d}. {line}")
        logging.error(f"Trouble reading configuration file {config_path}: {e}")
        sys.exit(1)


def _env_bool(name):
    """True when env var is set to 1 / true / yes (case-insensitive)."""
    return os.environ.get(name, "").lower() in ("1", "true", "yes")


def _address_tuple(address_string, default_port):
    """
    Parse 'host:port' or bare 'host' into (host, port).
    (Only used for stand-alone)
    """
    if "://" not in address_string:
        u = urlparse(f"http://{address_string}")
    else:
        u = urlparse(address_string)
    host = u.hostname or "localhost"
    port = u.port or default_port
    return host, port


# ---------------------------------------------------------------------------
# Shared initialisation — called by main() AND by gunicorn's on_starting hook
# ---------------------------------------------------------------------------

def init_app(
    *,
    config_path=None,
    database=None,
    token=None,
    address=None,
    enable_no_password=False,
):
    """
    Initialise module-level globals.

    Resolution order for every setting:
        explicit kwarg  →  env var  →  TOML value  →  built-in default

    Called from two places:
      • main()         – standalone; passes values parsed from the CLI
      • on_starting()  – gunicorn hook; all kwargs are None so env vars
                         and the TOML file drive configuration

    Returns (host, port) — only used by the standalone Flask server.
    """
    global db, jwt_token, no_password

    # ── TOML ──────────────────────────────────────────────────────────────
    cfg_path = config_path or os.environ.get("OWLOGGER_CONFIG") or _DEFAULT_CONFIG
    toml     = _read_toml(cfg_path)

    # ── no_password ────────────────────────────────────────────────────────
    no_password = (
        enable_no_password
        or _env_bool("OWLOGGER_NO_PASSWORD")
        or toml.get("no_password", False)
    )

    # ── JWT token ──────────────────────────────────────────────────────────
    jwt_token = token or os.environ.get("OWLOGGER_TOKEN") or toml.get("token")
    if jwt_token is None and not no_password:
        logging.warning(
            "Warning -- missing JWT token for POST/PUT. "
            "Supply --token, OWLOGGER_TOKEN, or set no_password if intentional."
        )

    # ── database ───────────────────────────────────────────────────────────
    db_path = (
        database
        or os.environ.get("OWLOGGER_DATABASE")
        or toml.get("database")
        or _DEFAULT_DB
    )
    db = Database(db_path)

    logging.debug(
        f"[init_app] config={cfg_path!r} db={db_path!r} "
        f"no_password={no_password} "
        f"jwt={'set' if jwt_token else 'unset'}"
    )

    # ── address (standalone only; gunicorn binds via gunicorn.conf.py) ────
    addr_str = (
        address
        or os.environ.get("OWLOGGER_ADDRESS")
        or toml.get("address")
        or _DEFAULT_ADDRESS
    )
    return _address_tuple(addr_str, _DEFAULT_PORT)


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
    except (ValueError, UnicodeDecodeError) as e:
        logging.error(f"Error decoding credentials: {e}")
        return True

    results = db.get_password(username)
    if len(results) != 1:
        return True

    return not bcrypt.checkpw(password.encode('utf-8'), results[0][0].encode('utf-8'))


def _auth_challenge():
    """Return a 401 Basic-Auth challenge response."""
    logging.info("Sending authentication challenge (401 Unauthorized)...")
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
    Returns (token_str, None) on success or (None, error_message) on failure.
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
                logging.warning(err)
                return Response(err, status=401)
            try:
                jwt.decode(h_token, jwt_token, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                logging.warning("Token expired")
                return Response("Token expired", status=401)
            except jwt.InvalidTokenError:
                logging.warning("Token invalid")
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
        return best_practice_headers(
            Response(f'<h1>404 Not Found</h1><p>{filename}</p>', status=404, content_type='text/html')
        )
    mime = ALLOWED_FILES[filename]
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return best_practice_headers(Response(f'File not found: {filename}', status=404))
    except PermissionError:
        logging.error(f'Permission denied to serve {filename} content')
        return best_practice_headers(Response(f'Access denied: {filename}', status=403))
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
    draw.rectangle([20, 20, width - 20, height - 20], outline=0, width=5)
    draw.text((width // 2, height // 2), "REMOTE DASHBOARD", fill=black)
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
    logging.debug(f"Sent {len(raw_buffer)} bytes")
    return best_practice_headers(resp)


@app.route('/test')
def frame_png():
    img = _create_image(800, 480)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    resp = send_file(buf, mimetype='image/png')
    logging.debug("Sent PNG")
    return best_practice_headers(resp)


# ---------------------------------------------------------------------------
# Main page (GET /)
# ---------------------------------------------------------------------------

@app.route('/')
@require_basic_auth
def index():
    date_str      = request.args.get('date', datetime.date.today().isoformat())
    page_type_raw = request.args.get('type', 'data')
    type_map      = {'week': 'week', 'plot': 'plot', 'stat': 'stat', 'month': 'month', }
    page_type     = type_map.get(page_type_raw, 'data')

    try:
        daystart = datetime.datetime.fromisoformat(date_str)
    except ValueError:
        daystart = datetime.datetime.combine(datetime.date.today(), datetime.time())

    logging.debug(f"GET / date={date_str} type={page_type}")

    html = _make_html(daystart, page_type)
    resp = Response(html, status=200, content_type='text/html')
    return best_practice_headers(resp)


def _make_html(daystart, page_type):
    # Data fetching
    if page_type == 'week':
        raw_data = db.week_data(daystart)
    elif page_type == 'month':
        raw_data = db.month_data(daystart) 
    else:
        raw_data = db.day_data(daystart)

    # Use json.dumps to handle quotes, escaping, and formatting
    now = datetime.datetime.now()
    js_vars = {
        "dayData": raw_data,
        "goodDays": [d[0] for d in db.distinct_days(daystart)],
        "goodMonths": [f"{daystart.year}-{m[0]}-01" for m in db.distinct_months(daystart)],
        "goodYears": [f"{y[0]}-01-01" for y in db.distinct_years()],
        "daystart": daystart.isoformat(),
        "page_type": page_type,
        "header_date": now.strftime('%m/%d/%Y'),
        "header_time": now.strftime('%H:%M'),
    }

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
                <a class="button" id="month" href="#" onclick="JumpTo.type('month')">Month</a>
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
        // Injecting the full config as a single JSON object is much safer
        var globals = {json.dumps(js_vars)};
        // Convert the date string back to a JS Date object
        globals.daystart = new Date(globals.daystart);
    </script>
</html>"""


# ---------------------------------------------------------------------------
# Data ingestion (POST / PUT)
# ---------------------------------------------------------------------------

@app.route('/', methods=['POST', 'PUT'])
@require_jwt
def receive_data():
    body = request.get_json(force=True)
    if body:
        logging.debug(f"POST {body}")
        name = body.get('name', 'unknown')
        data = body.get('data', '')
        if data:
            db.add(name, data)
        resp = Response('', status=200, content_type='text/html')
    else:
        resp = Response('Bad Request', status=400)
    return best_practice_headers(resp)


# ---------------------------------------------------------------------------
# Database class
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
        self.command('pragma journal_mode=wal')

    def get_version(self):
        try:
            records = self.fetch("""SELECT version FROM version WHERE id = 1""", None)
        except Exception:
            return 0
        if not records:
            return 0
        return records[0][0]

    def set_version(self, v):
        self.command(
            """INSERT INTO version(id, version) VALUES (1, ?)
               ON CONFLICT(id) DO UPDATE SET version = excluded.version;""",
            (v,))

    def set_password(self, username, password_hash):
        self.command(
            """INSERT INTO userlist(username, password_hash) VALUES (?, ?)
               ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash;""",
            (username, password_hash))

    def add(self, source, value):
        logging.debug(f"Adding _{value}")
        self.command(
            """INSERT INTO datalog(source, value) VALUES (?,?)""",
            (source, value))

    def day_data(self, day):
        nextday = day + datetime.timedelta(days=1)
        return self.fetch(
            """SELECT TIME(date, 'localtime') as t, source, value FROM datalog
               WHERE DATE(date,'localtime') BETWEEN DATE(?) AND DATE(?) ORDER BY t""",
            (day.isoformat(), nextday.isoformat()))

    def week_data(self, day):
        nextday  = day + datetime.timedelta(days=1)
        firstday = day + datetime.timedelta(days=-6)
        records = self.fetch(
            """SELECT strftime('%J',date,'localtime')-strftime("%J",?,'localtime') as t, source, value
               FROM datalog
               WHERE DATE(date,'localtime') BETWEEN DATE(?) AND DATE(?) ORDER BY t""",
            (firstday.isoformat(), firstday.isoformat(), nextday.isoformat()))
        logging.debug(records)
        return records

    def month_data(self, day):
        nextday  = day + datetime.timedelta(days=1)
        firstday = day + datetime.timedelta(days=-30)
        records = self.fetch(
            """SELECT strftime('%J',date,'localtime')-strftime("%J",?,'localtime') as t, source, value
               FROM datalog
               WHERE DATE(date,'localtime') BETWEEN DATE(?) AND DATE(?) ORDER BY t""",
            (firstday.isoformat(), firstday.isoformat(), nextday.isoformat()))
        logging.debug(records)
        return records

    def distinct_days(self, day):
        firstday = day + datetime.timedelta(days=-34)
        lastday  = day + datetime.timedelta(days=34)
        return self.fetch(
            """SELECT DISTINCT DATE(date,'localtime') as d FROM datalog
               WHERE DATE(date,'localtime') BETWEEN DATE(?) AND DATE(?) ORDER BY d""",
            (firstday.isoformat(), lastday.isoformat()))

    def distinct_months(self, day):
        year_start = f"{day.year}-01-01"
        year_end   = f"{day.year + 1}-01-01"
        return self.fetch(
            """SELECT DISTINCT strftime('%m', date,'localtime') AS m FROM datalog
               WHERE DATE(date,'localtime') >= ? AND DATE(date,'localtime') < ? ORDER BY m""",
            (year_start, year_end))

    def distinct_years(self):
        return self.fetch(
            """SELECT DISTINCT strftime('%Y', date,'localtime') AS y FROM datalog ORDER BY y""",
            None)

    def get_password(self, username):
        return self.fetch(
            """SELECT password_hash FROM userlist WHERE username=?""",
            (username,))

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def fetch(self, cmd, value_tuple=None):
        """SQL fetch command"""
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                if value_tuple is not None:
                    cursor.execute(cmd, value_tuple)
                else:
                    cursor.execute(cmd)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database reading error <{self.database}>: {e}")
            raise
        return None # Should never be reached

    def command(self, cmd, value_tuple=None):
        """SQL non-fetch command (add data or configure)"""
        try:
            with sqlite3.connect(self.database) as conn:
                cursor = conn.cursor()
                if value_tuple is not None:
                    cursor.execute(cmd, value_tuple)
                else:
                    cursor.execute(cmd)
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database writing error <{self.database}>: {e}")
            raise


# ---------------------------------------------------------------------------
# Password utility
# ---------------------------------------------------------------------------

def set_password(database, username, password):
    database.set_password(username, database.hash_password(password))


# ---------------------------------------------------------------------------
# Entry point  (standalone / development)
# ---------------------------------------------------------------------------

def main(sysargs):
    # Pass 1: locate --config early so TOML values seed argparse defaults
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument(
        "-c", "--config",
        required=False, default=None,
        dest="config", type=str, nargs="?",
        help=f"TOML configuration file. Default={_DEFAULT_CONFIG}",
    )
    pre_args, remaining_argv = pre_parser.parse_known_args()

    toml = _read_toml(pre_args.config or _DEFAULT_CONFIG)

    # Pass 2: full argument set, seeded from TOML where available
    parser = argparse.ArgumentParser(
        parents=[pre_parser],
        prog="owlogger_flask",
        description="Logs 1-wire data to a database that can be viewed on the web. Flask edition.",
        epilog="Repository: https://github.com/alfille/owlogger",
    )
    parser.add_argument(
        '-a', '--address',
        required=False, default=toml.get("address", _DEFAULT_ADDRESS),
        dest="address", nargs='?', type=str,
        help=f'Server IP address and port. Default={_DEFAULT_ADDRESS}',
    )
    parser.add_argument(
        '-t', '--token',
        required=False, default=toml.get("token"),
        dest="token", type=str, nargs='?',
        help='JWT secret token to match with owpost/generalpost.',
    )
    parser.add_argument(
        '-f', '--file',
        required=False, default=toml.get("database", _DEFAULT_DB),
        dest="database", type=str, nargs='?',
        help=f'Database file location. Default={_DEFAULT_DB}',
    )
    parser.add_argument(
        "-d", "--debug",
        required=False, default=toml.get("debug", False),
        dest="debug", action="store_true",
        help="Print debugging information",
    )
    parser.add_argument(
        "--no_password",
        required=False, default=toml.get("no_password", False),
        dest="no_password", action="store_true",
        help="Turns off password protection",
    )

    args = parser.parse_args(remaining_argv)

    logging.root.setLevel(logging.DEBUG if args.debug else logging.INFO)
    logging.debug(f"sysargs={sysargs}, args={args}")

    host, port = init_app(
        config_path=pre_args.config,
        database=args.database,
        token=args.token,
        address=args.address,
        enable_no_password=args.no_password,
    )

    logging.info(f"Server started {host}:{port}")
    app.run(host=host, port=port, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
