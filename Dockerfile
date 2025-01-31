# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \n    PYTHONUNBUFFERED=1 \n    FLASK_APP=wsgi.py \n    FLASK_ENV=production \n    PORT=3000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \n    gcc \n    libpq-dev \n    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /var/log/webapp1 && \n    chmod -R 777 /var/log/webapp1

# Expose the port
EXPOSE $PORT

# Command to run the application
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "4", "--bind", "0.0.0.0:3000", "wsgi:app"]