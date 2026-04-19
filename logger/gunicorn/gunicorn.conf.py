# gunicorn.conf.py
#
# Gunicorn configuration for owlogger_flask.
#
# Direct use (no systemd):
#   gunicorn -c gunicorn.conf.py owlogger_flask:app
#
# Via systemd (recommended for production):
#   owlogger.service runs this command.  Systemd injects env vars from
#   /etc/owlogger/owlogger.env before Python starts, so init_app() in
#   the on_starting hook picks them up automatically.
#
# Caddy reads from the same UNIX socket defined by `bind` below.
# The socket path must match the one in Caddyfile.

# ── Network ───────────────────────────────────────────────────────────────
# UNIX socket: lower overhead than TCP for same-host proxy traffic and
# exposes no network port.  The socket directory is created by systemd's
# RuntimeDirectory= directive (see owlogger.service).
bind = "unix:/run/owlogger/owlogger.sock"

# ── Workers ───────────────────────────────────────────────────────────────
# SQLite WAL supports concurrent readers but serialises writers, so keep
# the worker count low.  Threads add concurrency at lower overhead.
workers      = 2
threads      = 4
worker_class = "sync"

# ── Timeouts ──────────────────────────────────────────────────────────────
timeout          = 30
graceful_timeout = 30
keepalive        = 5

# ── Logging ───────────────────────────────────────────────────────────────
# "-" → stdout / stderr, captured by the systemd journal.
accesslog = "-"
errorlog  = "-"
loglevel  = "info"

# ── Process name ──────────────────────────────────────────────────────────
proc_name = "owloggerf"

# ── Hooks ─────────────────────────────────────────────────────────────────

def on_starting(server):
    """
    Called once in the arbiter (master) before workers are forked.
    Reads env vars injected by systemd and/or the TOML config file,
    then initialises globals that every worker will inherit.
    """
    from owlogger_flask import init_app
    init_app()


def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")
