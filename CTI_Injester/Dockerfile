FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy offline packages and requirements
COPY offline-packages/ /app/offline-packages/
COPY requirements.txt .

# Install from offline packages (no internet required)
RUN pip install --no-index --find-links /app/offline-packages -r requirements.txt

# Copy application code
COPY run.py .
COPY templates templates/
COPY plugin plugin/

# Create necessary directories
RUN mkdir -p flask_session plugin/tor/data plugin/malwarebazaar/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_PASSWORD=admin
ENV SECRET_KEY=change-this-in-production

# Expose port
EXPOSE 5055

# Run the application
CMD ["python", "run.py"]