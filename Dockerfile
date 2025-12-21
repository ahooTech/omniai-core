# Dockerfile
# Your app runs the same way everywhere (no “it works on my machine” issues)
# It’s lightweight and secure (no extra bloat)
# It’s ready for production (proper packaging, clear start command)

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY src/ ./src/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "omniai.main:app", "--host", "0.0.0.0", "--port", "8000"]