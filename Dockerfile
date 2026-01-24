# Dockerfile
# Your app runs the same way everywhere (no “it works on my machine” issues)
# It’s lightweight and secure (no extra bloat)
# It’s ready for production (proper packaging, clear start command)

FROM python:3.11-slim

# Install system dependencies FIRST (best practice) to be used by database commands in test
# ✅ Install ALL system dependencies in ONE layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        postgresql-client \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
    
# 🔒 Critical: Patch pip BEFORE installing Python packages
RUN pip install --no-cache-dir --upgrade "pip>=25.2"

WORKDIR /app

# Copy all source and config for editable install
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY tests/ ./tests/ 
COPY scripts/ ./scripts/

# 💡 New: Accept a build arg to decide whether to install test dependencies
ARG INSTALL_DEV=false
    
# Replace the two RUN lines with this:
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        # if variable in test is true install main deps + dev deps
      pip install --no-cache-dir --only-binary=all -e ".[dev]"; \
    else \
    # if variable in test is false install main deps only
      pip install --no-cache-dir --only-binary=all -e .; \
    fi

COPY scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# Make the app user own the directory (optional but clean)
RUN chown -R app:app /app

# Switch to non-root user
USER app

# ✅ Set runtime configuration via environment variables
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV UVICORN_RELOAD=false

EXPOSE 8000



CMD ["/app/start.sh"]
# CMD ["python", "-m", "uvicorn", "omniai.main:app", "--host", "0.0.0.0", "--port", "8000"]


# This is my Docker file that is built by either docker-compose-test.yml for testing or docker-compose.yml for real world