[Unit]
Description=Webapp1 Gunicorn Service
After=network.target
Requires=network.target

[Service]
Type=notify
User=saif
Group=saif
WorkingDirectory=/home/saif/webapp1

# Environment setup
Environment="PATH=/home/saif/webapp1/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/home/saif/webapp1"
Environment="PYTHONUNBUFFERED=1"

# Create log directory with proper permissions (as root)
PermissionsStartOnly=true
ExecStartPre=!/bin/bash -c 'mkdir -p /var/log/gunicorn && chown -R saif:saif /var/log/gunicorn && chmod 755 /var/log/gunicorn'

# Start Gunicorn
ExecStart=/home/saif/webapp1/venv/bin/gunicorn -c /home/saif/webapp1/gunicorn.conf.py wsgi:app

# Process management
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=35
KillMode=mixed
KillSignal=SIGTERM
SendSIGKILL=yes

# Logging
StandardOutput=append:/var/log/gunicorn/output.log
StandardError=append:/var/log/gunicorn/error.log

[Install]
WantedBy=multi-user.target 