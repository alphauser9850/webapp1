import multiprocessing

# Bind to the socket
bind = 'unix:/home/saif/webapp1/app.sock'

# Number of workers
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = 'sync'  # You can change this to 'gevent' or 'eventlet' if needed

# Timeout settings
timeout = 30

# Log level
loglevel = 'info'

# Access log file
accesslog = '/home/saif/webapp1/logs/gunicorn-access.log'

# Error log file
errorlog = '/home/saif/webapp1/logs/gunicorn-error.log'

# Daemonize the Gunicorn process (if needed)
# daemon = True

# Preload the application
preload_app = True

# Enable keep-alive
keepalive = 5 