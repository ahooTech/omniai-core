# Dockerfile
# Your app runs the same way everywhere (no “it works on my machine” issues)
# It’s lightweight and secure (no extra bloat)
# It’s ready for production (proper packaging, clear start command)

FROM python:3.11-slim


WORKDIR /app

# ✅ COPY EVERYTHING needed for editable install BEFORE running pip
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# ✅ Now install — all files are present. Install dependencies AS ROOT (so pip can write)
RUN pip install --no-cache-dir -e .

# Create non-root user after install
RUN addgroup --system app && adduser --system --group app

# Make the app user own the directory (optional but clean)
# RUN chown -R app:app /app

# Switch to non-root user for runtime
USER app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "omniai.main:app", "--host", "0.0.0.0", "--port", "8000"]