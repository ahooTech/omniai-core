```markdown
# [ADR-006] Select FastAPI as Core Backend Framework

## Status
✅ Accepted

## Context
OMNIAI Core requires a modern Python web framework that:
- Supports **asynchronous I/O** for high concurrency (e.g., DB calls, external APIs)
- Provides **automatic request/response validation** to prevent invalid states
- Generates **interactive API documentation** for developers and testers
- Enforces **type safety** with minimal boilerplate
- Delivers **production-grade performance** out of the box
- Integrates cleanly with **SQLAlchemy 2.0 async**, **Pydantic v2**, and **cloud deployment**

Key constraints:
- Solo founder velocity (minimal config, fast iteration)
- Future scalability to AI workloads (LLM agents, RAG pipelines)
- Compatibility with structured logging, middleware, and observability

## Decision
We select **FastAPI (v0.100+)** as the core backend framework.

### Justification by Requirement

| Requirement | FastAPI Solution |
|-----------|------------------|
| **Async Support** | Native `async`/`await` with Starlette under the hood |
| **Validation** | Pydantic v2 models auto-validate requests/responses |
| **Documentation** | Auto-generated OpenAPI + Swagger UI at `/docs` |
| **Type Safety** | Full mypy compatibility; type hints drive validation |
| **Performance** | Benchmarks show ~3x faster than Flask/Django (TechEmpower) |
| **Middleware** | Starlette-compatible middleware stack (logging, auth, rate limiting) |
| **Ecosystem** | First-class support for SQLAlchemy async, structlog, slowapi |

### Key Implementation Patterns Used
- **Dependency Injection**:  
  ```python
  def get_db(session: AsyncSession = Depends(db_session)):
      yield session
  ```
- **Automatic Error Handling**:  
  Pydantic validation errors → `422 Unprocessable Entity` with details
- **Route Organization**:  
  Modular routers (`auth`, `users`) mounted under `/v1`
- **Async Endpoints**:  
  All routes use `async def` for non-blocking I/O
- **OpenAPI Customization**:  
  Automatic docs include security schemes (JWT bearer)

## Consequences

### Good
- **Developer Velocity**: No manual validation or doc writing — focus on business logic
- **Fewer Bugs**: Type-driven validation catches 80% of input errors at boundary
- **Self-Documenting API**: `/docs` always up-to-date — critical for frontend/AI agent integration
- **High Throughput**: Handles 1K+ RPM on modest hardware (verified via load testing)
- **Future-Proof**: Async foundation ready for LLM streaming, WebSockets, background agents

### Bad
- **Smaller Community**: Fewer Stack Overflow answers vs Flask/Django
- **Rapid Evolution**: Breaking changes between major versions (mitigated by pinning)
- **Learning Curve**: Requires understanding of async/await and Pydantic models

### Neutral
- **Opinionated**: Less “do it your way” than Flask — but enforces best practices
- **Dependency Count**: Adds Starlette, Pydantic, Uvicorn — but all are lightweight

## Alternatives Considered

### Flask
- ✅ Huge community, simple for basic apps
- ❌ No native async support (requires complex workarounds)
- ❌ Manual validation (error-prone)
- ❌ No auto-generated docs without extensions
- ❌ Slower for I/O-bound workloads (synchronous by default)

### Django
- ✅ “Batteries included” (ORM, admin, auth)
- ❌ Overkill for API-only service (no templates, sessions needed)
- ❌ Async support still maturing (Django 4.1+)
- ❌ Heavyweight for microservice architecture
- ❌ ORM not compatible with SQLAlchemy ecosystem (blocks Alembic, async)

### Starlette (Bare Metal)
- ✅ Maximum control and minimal overhead
- ❌ No automatic validation or OpenAPI
- ❌ Requires building everything from scratch (routing, serialization)
- ❌ Slower development velocity — not viable for solo founder

### Sanic
- ✅ Async-native and fast
- ❌ Smaller ecosystem, less mature tooling
- ❌ No Pydantic integration out of the box
- ❌ Riskier long-term maintenance

## Verdict
FastAPI delivers the **optimal balance of speed, safety, and scalability** for OMNIAI Core’s mission:  
> **Build a sovereign, observable, multi-tenant AI foundation — fast.**

Its async-native, type-safe, self-documenting nature makes it the **only rational choice** for a modern AI engineering platform.

## References
- FastAPI Official: https://fastapi.tiangolo.com/
- TechEmpower Benchmarks: https://www.techempower.com/benchmarks/
- OMNIAI Core Implementation:  
  - [`main.py`](https://github.com/ahooTech/omniai-core)  
  - [`api/v1/auth.py`](https://github.com/ahooTech/omniai-core)
- Live Docs: https://omniai-web.onrender.com/docs
```