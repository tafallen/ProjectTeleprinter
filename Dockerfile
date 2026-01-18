# Dockerfile for Project Telex Node
# Factory template: Multi-stage build for Python application

# Stage 1: Builder
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Create non-root user
RUN groupadd -r telex && useradd -r -g telex telex

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/telex/.local

# Copy application source
COPY --chown=telex:telex src/ /app/src/
COPY --chown=telex:telex pyproject.toml /app/

# Create necessary directories
RUN mkdir -p /app/telex_data /etc/telex && \
    chown -R telex:telex /app /etc/telex

# Update PATH to include local pip installs
ENV PATH=/home/telex/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER telex

# Expose default Telex port
EXPOSE 8023

# Run the Telex server
CMD ["python", "-m", "telex.main"]
