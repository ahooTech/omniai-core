# Dockerfile
# Your app runs the same way everywhere (no “it works on my machine” issues)
# It’s lightweight and secure (no extra bloat)
# It’s ready for production (proper packaging, clear start command)

FROM python:3.11-slim

WORKDIR /app

# Copy all source and config for editable install
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# 💡 New: Accept a build arg to decide whether to install test dependencies
ARG INSTALL_DEV=false

# Install main dependencies (always)
RUN pip install --no-cache-dir -e .

# Install test dependencies only if requested
RUN if [ "$INSTALL_DEV" = "true" ]; then \
      pip install --no-cache-dir -e ".[dev]"; \
    fi

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# Make the app user own the directory (optional but clean)
# RUN chown -R app:app /app

# Switch to non-root user
USER app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "omniai.main:app", "--host", "0.0.0.0", "--port", "8000"]