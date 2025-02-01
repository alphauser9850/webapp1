# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    FLASK_ENV=production \
    PORT=3000 \
    SESSION_FILE_DIR=/tmp/flask_session \
    EVENTLET_NO_GREENDNS=yes

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /var/log/webapp1 && \
    chmod -R 777 /var/log/webapp1 && \
    mkdir -p /var/log/gunicorn && \
    chmod -R 777 /var/log/gunicorn && \
    mkdir -p /tmp/flask_session && \
    chmod -R 777 /tmp/flask_session && \
    mkdir -p instance && \
    chmod -R 777 instance

# Initialize the database and create admin user
RUN flask db upgrade || true

# Expose the port
EXPOSE $PORT

# Command to run the application
CMD ["sh", "-c", "flask db upgrade && if [ ! -z \"$ADMIN_EMAIL\" ] && [ ! -z \"$ADMIN_PASSWORD\" ]; then flask create-admin --email \"$ADMIN_EMAIL\" --password \"$ADMIN_PASSWORD\" || true; fi && gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --error-logfile /var/log/gunicorn/error.log --access-logfile /var/log/gunicorn/access.log --timeout 120 wsgi:app"]