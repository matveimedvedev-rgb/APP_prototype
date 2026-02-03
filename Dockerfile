# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files (if you have any)
RUN python manage.py collectstatic --noinput || true

# Run migrations
RUN python manage.py migrate --noinput || true

# Expose port (Cloud Run uses PORT env var)
ENV PORT=8080
EXPOSE 8080

# Use gunicorn to serve the app
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 config.wsgi:application

