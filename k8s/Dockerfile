FROM python:3.10-slim

WORKDIR /app

# Install git and other dependencies if needed
RUN apt-get update && apt-get install -y git openssl && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies and the package
RUN pip install --no-cache-dir . uvicorn

# Copy entrypoint script
COPY k8s/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port (default 8000, now configurable)
EXPOSE 4443

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["chaimcp"]
