FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow (avatar processing)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy static files (avatars, etc.)
COPY static/ ./static/

# Create directories for persistent data
RUN mkdir -p /app/data /app/static/avatars

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
