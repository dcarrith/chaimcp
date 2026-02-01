#!/bin/sh
set -e

# Generate self-signed certificate if not present
if [ ! -f /app/server.key ] || [ ! -f /app/server.crt ]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -newkey rsa:4096 -keyout /app/server.key -out /app/server.crt -days 365 -nodes -subj '/CN=chiamcp'
fi

# Execute the application
exec "$@"
