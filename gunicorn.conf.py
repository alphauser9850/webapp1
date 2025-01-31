import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5001"
backlog = 1024

# Worker processes - optimized for WebSocket
workers = 1  # Single worker for WebSocket
worker_class = 'eventlet'
worker_connections = 1000
threads = 1

# Timeouts and keep-alive
timeout = 120
keepalive = 2
graceful_timeout = 30

# Process management
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "webapp1"
pidfile = "/tmp/webapp1.pid"

# Server mechanics
daemon = False
umask = 0
user = None
group = None
tmp_upload_dir = None

# Worker configuration
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = "*"

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_fork(server, worker):
    """Called just prior to forking the worker."""
    pass

def pre_exec(server):
    """Called just prior to forking off a secondary master process during things like config reloading."""
    server.log.info("Forking master process")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker aborted (pid: {worker.pid})")

def child_exit(server, worker):
    """Called just after a worker has been exited, in the worker process."""
    server.log.info(f"Worker exited (pid: {worker.pid})")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    try:
        if os.path.exists(server.pidfile):
            os.remove(server.pidfile)
    except Exception:
        pass 