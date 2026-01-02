"""
OMNIAI Health Check API

This lightweight endpoint will evolve through Phase 1 as follows:

✅ [DONE] 1. Basic health check
   - Returns {"status": "ok"} for liveness

🔜 [PHASE 1: Observability]
   - Add detailed health indicators:
       • Database connectivity
       • Redis availability
       • External dependency status (e.g., SMS gateway)
   - Implement /v1/ready (readiness) vs /v1/live (liveness)

🔜 [PHASE 1: Security]
   - Add auth requirement for detailed health (public vs private health)

🔜 [PHASE 1: Backend Engineering]
   - Add version info: {"version": "1.0.0", "commit": "..."}
   - Add build timestamp and environment (dev/staging/prod)

🔜 [PHASE 1: System Architecture]
   - Integrate with circuit breaker status (e.g., "db: degraded")
   - Report tenant count or system load metrics (if safe)

🔜 [PHASE 2+ Integration]
   - Add AI model status: "embedding_engine: ready"
   - Report vector DB connectivity

NOTE: Keep this endpoint lightweight and dependency-minimal.
Never let health checks trigger expensive operations by default.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "omniai-core"}
