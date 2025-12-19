# src/omniai/db/session.py
# PHASE 1 PLACEHOLDER — will be replaced with real DB session in Database Engineering phase

from typing import Generator

def get_db() -> Generator:
    """
    Placeholder DB session generator.
    In Phase 1 (Database Engineering), this will return a real SQLAlchemy session.
    For now, it yields a mock session object.
    """
    # Mock session object with .query() method
    class MockSession:
        def query(self, model):
            return MockQuery(model)

        def close(self):
            pass

    class MockQuery:
        def __init__(self, model):
            self.model = model

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            # For testing middleware: return a mock tenant if ID matches
            from omniai.models.organization import Organization
            if hasattr(self, '_mock_id') and self._mock_id == "ng-lagos-moh-2025":
                return Organization(id="ng-lagos-moh-2025", name="Lagos State Ministry of Health")
            return None

    session = MockSession()
    try:
        yield session
    finally:
        session.close()