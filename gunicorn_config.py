import multiprocessing

# Binding
bind = "unix:/tmp/webapp1.sock"  # Unix socket for Nginx to communicate with
# bind = "0.0.0.0:8000"  # Alternatively, bind directly to a port

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "eventlet"  # Using eventlet for async support
worker_connections = 1000

# Timeout
timeout = 120  # Increase timeout for long-running tasks

# Logging
accesslog = "/var/log/webapp1/access.log"
errorlog = "/var/log/webapp1/error.log"
loglevel = "info"

# SSL (if not terminating SSL at nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Process Naming
proc_name = "webapp1"

# Server Mechanics
daemon = False  # Don't daemonize when running with systemd
pidfile = "/tmp/webapp1.pid"
umask = 0o007
user = None  # Will be set by systemd service
group = None  # Will be set by systemd service

# Server Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called before code is reloaded."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    pass 