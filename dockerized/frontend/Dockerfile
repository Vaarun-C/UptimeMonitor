# Dockerfile for Streamlit Frontend
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
COPY frontend.py .

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "frontend.py", "--server.address", "0.0.0.0", "--server.port", "8501"]