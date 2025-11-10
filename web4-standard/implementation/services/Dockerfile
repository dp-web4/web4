FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY *.py ./
COPY ../reference ./reference/

# Expose ports (all services)
EXPOSE 8001 8002 8003 8004 8005 8006

# Health check (overridden by docker-compose for specific port)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command (overridden by docker-compose)
CMD ["python", "identity_service.py"]
