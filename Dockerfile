# Use official Python 3.12 slim image
FROM python:3.12-slim

# Install Node.js for JS sandbox support
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python packages
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend, templates, sandbox, and tests
COPY backend /app/backend
COPY templates /app/templates
COPY sandbox /app/sandbox

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV SANDBOX_TIMEOUT=10
ENV MAX_DEBUG_ATTEMPTS=3

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
