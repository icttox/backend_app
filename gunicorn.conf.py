import multiprocessing
import os

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/settings.html

# Server socket
bind = "0.0.0.0:8099"

# Worker processes - recommended formula is (2 x $num_cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Worker options
worker_class = "sync"  # Since Django is synchronous
worker_connections = 1000
timeout = 120  # Increased from default 30 seconds to handle longer requests
keepalive = 5

# Server mechanics
daemon = False  # Don't daemonize in Docker
pidfile = None  # Don't create a pidfile in Docker
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"  # Log to stdout, Docker will handle logging
errorlog = "-"   # Log to stderr, Docker will handle logging
loglevel = "info"
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# Process naming
proc_name = None

# Server hooks
def on_starting(server):
    pass

def on_exit(server):
    pass

# Handle workers that have failed to boot properly
max_requests = 1000
max_requests_jitter = 50  # Add randomness to max_requests to avoid all workers restarting at once

# Prevent the worker from handling any other requests after it's received a restart signal
graceful_timeout = 30

# Use a proper statsd client if available
# statsd_host = "localhost:8125"
# statsd_prefix = "gunicorn"

# Enable support for HTTP/2
forwarded_allow_ips = '*'
