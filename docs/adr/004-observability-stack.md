```markdown
# [ADR-004] Structured Observability with Context-Aware Logging, Health Checks, and Metrics

## Status
✅ Accepted

## Context
OMNIAI Core must be **observable in production** to:
- Diagnose failures quickly during incidents
- Trace user journeys across requests (even in multi-tenant context)
- Monitor system health for auto-recovery (e.g., Render restarts)
- Measure performance and error rates at scale
- Support audit and security investigations

Requirements:
- **Machine-readable logs** for ingestion into cloud log systems
- **Automatic context propagation**: `user_id`, `org_id`, `trace_id`
- **Standardized health endpoints** for load balancers
- **Minimal performance overhead**
- **Zero sensitive data leakage** in logs

## Decision
We implement a lightweight but production-grade observability stack using:
1. **Structured logging** with `structlog` (JSON output)
2. **Automatic context binding** via middleware
3. **Standard health endpoints**: `/health` and `/health/ready`
4. **Prometheus-compatible metrics** (minimal initial set)

### Detailed Implementation

#### 1. Structured Logging (`structlog`)
- **Format**: JSON with consistent fields:
  ```json
  {
    "timestamp": "2026-01-23T05:13:02Z",
    "level": "info",
    "event": "login_success",
    "trace_id": "8a8d6cf5-...",
    "user_id": "usr_28ed66f9...",
    "org_id": "org_abc123",
    "client_ip": "10.20.152.68"
  }
  ```
- **Logger setup**:  
  - Console renderer in dev  
  - JSON renderer in production (via env flag)
- **No sensitive data**: Passwords, tokens never logged
- **Event naming**: Consistent, searchable event names (`auth_login_success`, `org_deleted`, etc.)

#### 2. Context Propagation Middleware
- **Trace ID**: Generated per request → attached to all logs in that request
- **User/Org Context**: Bound after auth middleware resolves identity:
  ```python
  # In middleware.py
  structlog.contextvars.bind_contextvars(
      user_id=current_user.id,
      org_id=current_org.id,
      trace_id=request.state.trace_id
  )
  ```
- **Automatic cleanup**: Context reset after each request
- **Health endpoints**: Exclude user/org context (no auth required)

#### 3. Health Endpoints
- **`GET /v1/health`**  
  - Purpose: Is the process running?  
  - Response: `{"status": "ok"}`  
  - No dependencies (never fails unless app crashed)
- **`GET /v1/health/ready`**  
  - Purpose: Is the app ready to serve traffic?  
  - Checks: Database connectivity  
  - Response: `{"status": "ready", "service": "omniai-core"}` or `503` if DB unreachable
- **Used by**: Render health checks, Kubernetes probes, load balancers
- **Startup probe**: Waits for DB connection before marking app as ready

#### 4. Metrics (Initial Set)
- **Exposed via**: Standard HTTP endpoint (`/metrics` — not yet implemented but designed for)
- **Planned metrics**:
  - `http_requests_total{method, endpoint, status}`
  - `http_request_duration_seconds{endpoint}`
  - `auth_login_attempts_total{outcome}`
- **Library**: Compatible with Prometheus client (to be added in Phase 2)
- **Current implementation**: Custom middleware tracks request count/duration

#### 5. Log Destinations
- **Local dev**: Pretty-printed console logs
- **Production**: JSON logs shipped to cloud provider (Render → CloudWatch equivalent)
- **Retention**: Managed by cloud provider (Render retains logs for 7 days)

#### 6. Security & Compliance
- **PII handling**: No email, password, or token in logs
- **Audit trail**: All auth and org lifecycle events logged with `trace_id`
- **Error masking**: Generic error messages in responses; full details only in logs

## Consequences

### Good
- **Debuggability**: Full request context in every log line → no more “which user caused this?”
- **Incident response**: Trace ID allows reconstruction of entire user session
- **Cloud-native**: Works out-of-the-box with Render, AWS, GCP log ingestion
- **Security-safe**: No PII or secrets in logs by design
- **Low overhead**: `structlog` adds <1ms latency

### Bad
- **Learning curve**: New team members must understand contextvars pattern
- **No built-in dashboard**: Requires Grafana/Prometheus for metrics (Phase 2)

### Neutral
- **Log volume**: Slightly higher than unstructured logs (worth the tradeoff)
- **Dependency**: Adds `structlog` to requirements (lightweight)

## Alternatives Considered

### Standard Library `logging`
- ❌ Not structured → hard to query in cloud
- ❌ No automatic context binding
- ❌ Requires manual formatting for JSON

### OpenTelemetry (OTel)
- ✅ Industry standard
- ❌ Overkill for Phase 1 (adds significant complexity)
- ❌ Requires collector infrastructure
- ⚠️ Planned for Phase 2 when scaling to microservices

### ELK-Specific Logging
- ❌ Vendor lock-in
- ❌ Unnecessary when cloud providers offer native log ingestion

## References
- OMNIAI Core Logging:  
  - [`src/omniai/core/logging.py`](https://github.com/ahooTech/omniai-core)  
  - [`src/omniai/core/logging_middleware.py`](https://github.com/ahooTech/omniai-core)
- Health Endpoint Code: [`/v1/health/ready` implementation](https://omniai-web.onrender.com/v1/health/ready)
- Render Logs: Live JSON logs visible in Render dashboard
- structlog Docs: https://www.structlog.org/
```