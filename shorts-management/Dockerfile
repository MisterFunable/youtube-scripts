FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY web_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files (just the shorts folder)
COPY . .

# Create templates directory and copy template
RUN mkdir -p templates
COPY templates/index.html templates/

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "web_ui.py"]
