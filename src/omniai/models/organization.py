# src/omniai/models/organization.py
# PHASE 1 PLACEHOLDER — will be replaced with real SQLAlchemy model later

from dataclasses import dataclass

@dataclass
class Organization:
    id: str
    name: str
    # Later: add created_at, status, language, etc.