FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
# pyATS/Genie requires several system libraries including paramiko dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    iputils-ping \
    openssh-client \
    telnet \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install dependencies based on requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port (must match run_web.py)
EXPOSE 5000

# Create volume mount points for persistence
VOLUME /app/snapshots
VOLUME /app/uploads
VOLUME /app/instance

# Run the application
CMD ["python", "run_web.py"]
