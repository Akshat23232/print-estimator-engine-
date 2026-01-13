# Multi-stage build for smaller production image
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies in a virtual environment for clean copying
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/

# Create non-root user for security
# NOTE: In production, always run as non-root
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run with uvicorn
# NOTE: In production, use gunicorn with uvicorn workers for better performance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
