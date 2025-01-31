import multiprocessing

# Binding
bind = "0.0.0.0:3000"  # Bind to all interfaces on port 3000

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "eventlet"  # Using eventlet for async support
worker_connections = 1000

# Timeout
timeout = 120

# Logging
accesslog = "/var/log/webapp1/access.log"
errorlog = "/var/log/webapp1/error.log"
loglevel = "info"

# Process Naming
proc_name = "webapp1"

# Server Mechanics
daemon = False
pidfile = None
umask = 0o007
user = None
group = None

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