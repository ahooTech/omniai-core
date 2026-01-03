#!/bin/sh
set -e

# Build the command dynamically
CMD="uvicorn omniai.main:app --host ${UVICORN_HOST:-0.0.0.0} --port ${UVICORN_PORT:-8000}"

# Only add --reload if explicitly set to "true"
if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
    CMD="$CMD --reload"
fi

exec $CMD