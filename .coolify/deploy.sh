#!/bin/bash

# Run database migrations
flask db upgrade

# Create admin user if ADMIN_EMAIL and ADMIN_PASSWORD are set
if [ ! -z "$ADMIN_EMAIL" ] && [ ! -z "$ADMIN_PASSWORD" ]; then
    flask create-admin --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD"
fi

# Additional deployment steps can be added here 