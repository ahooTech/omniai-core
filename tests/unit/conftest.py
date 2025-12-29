# tests/conftest.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load test env ONCE before any test runs
env_path = Path(__file__).parent.parent / ".env.test"
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    # Fallback: require explicit env vars in CI
    pass