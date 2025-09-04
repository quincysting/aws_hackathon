# Use ARM64 Python base image as required by Bedrock AgentCore
FROM --platform=linux/arm64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV AWS_DEFAULT_REGION=us-west-2

# Expose the required port for Bedrock AgentCore
EXPOSE 8080

# Run the FastAPI application
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]