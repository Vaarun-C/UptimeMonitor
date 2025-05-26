# Dockerfile for FastAPI Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api_backend.py .
COPY constants.py .
COPY database_manager.py .
COPY monitoring_service.py .
COPY notification_service.py .

# Create directory for SQLite database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/uptime_monitor.db

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api_backend:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]