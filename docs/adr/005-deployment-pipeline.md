```markdown
# [ADR-005] Cloud-Native Deployment Pipeline with Docker, GitHub Actions, and Render

## Status
✅ Accepted

## Context
OMNIAI Core must be deployable:
- **Reliably**: Every commit is tested before merge
- **Securely**: Secrets never exposed in code or logs
- **Reproducibly**: Same artifact runs in dev, CI, and prod
- **Efficiently**: Fast feedback loop (<5 min from push to deploy)
- **Cost-effectively**: Free tier viable for early validation

## Requirements:
- Automated testing (unit, integration, security)
- Containerized build for environment parity
- One-command local setup (`docker-compose up`)
- Public HTTPS endpoint with auto-renewing TLS
- Zero manual deployment steps
- **Observability**: Structured logs shipped to cloud provider

## Decision
We implement a fully automated, cloud-native pipeline using:
1. **Multi-stage Docker builds** for minimal, secure images
2. **GitHub Actions** for CI/CD with quality gates
3. **Render** as the production hosting platform (web + PostgreSQL)

### Detailed Implementation

#### 1. Docker Strategy
- **Multi-stage build**:
  - **Builder stage**: Installs dev dependencies, runs static analysis
  - **Runtime stage**: Copies only production dependencies + app code
- **Security hardening**:
  - Non-root user (`uid=1000`)
  - `.dockerignore` excludes secrets, cache, IDE files
  - Minimal base image (`python:3.11-slim`)
- **Local development**:  
  - `docker-compose.yml` defines `app`, `postgres` services  
  - Volumes for DB persistence during dev
  - Health check against `/v1/health/ready`
- **Image tagging**: `ghcr.io/ahooTech/omniai-core:sha-${{ github.sha }}`

#### 2. GitHub Actions CI/CD
- **Trigger**: On every `push` to `main`
- **Pipeline stages**:
  1. **Test**: `pytest` with isolated `omniai_test` database
  2. **Lint**: `ruff check`
  3. **Type Check**: `mypy`
  4. **Security Scan**: `bandit` (code) + `safety` (deps)
  5. **Build**: Docker image with SHA tag
  6. **Push**: Image published to GitHub Container Registry (GHCR)
- **Quality gates**: Any step failure blocks deployment
- **Caching**: Dependency caches speed up repeat runs
- **Coverage**: Enforces >90% test coverage

#### 3. Render Deployment
- **Web Service**:
  - Pulls latest Docker image from GHCR
  - Auto-redeploys on new image push
  - Free TLS certificate (HTTPS enforced)
  - Health checks against `/v1/health/ready`
  - **Structured JSON logs** visible in Render dashboard
- **PostgreSQL**:
  - Managed database instance (free tier)
  - Encrypted at rest and in transit
  - Connection string via `DATABASE_URL` env var
  - Auto-backups enabled
- **Secrets Management**:
  - All secrets (JWT key, DB URL) set in Render dashboard
  - Never committed to Git or stored in Docker layers
- **Environment Parity**: Same Docker image runs in CI and prod

#### 4. Local-to-Prod Consistency
- **Single source of truth**: `Dockerfile` defines runtime environment
- **Config via env vars**: 12-factor compliant (`DATABASE_URL`, `JWT_SECRET_KEY`)
- **No “works on my machine”**: Dev, CI, prod all use containers
- **Health readiness**: App waits for DB before accepting traffic

#### 5. Observability Integration
- **Logs**: JSON-formatted, shipped to Render → searchable in dashboard
- **Metrics**: Custom middleware tracks request count/duration (Prometheus-ready)
- **Tracing**: `trace_id` in every log line for request correlation

## Consequences

### Good
- **Fast iteration**: Push to `main` → live in <5 minutes
- **High quality**: Broken code never reaches prod
- **Security**: Secrets never in code; minimal attack surface
- **Cost**: $0 for early validation (Render free tier)
- **Debugging**: Local `docker-compose` mirrors prod exactly
- **Audit-ready**: Full log trail with context

### Bad
- **Vendor lock-in (mild)**: Render-specific features may require migration effort later
- **Cold starts**: Free tier has sleep/wake latency (acceptable for MVP)

### Neutral
- **Docker overhead**: Small learning curve for new contributors
- **Image size**: ~200MB runtime image (optimized but not ultra-minimal)

## Alternatives Considered

### AWS ECS / Fargate
- ✅ Full control, enterprise-ready
- ❌ Complex setup (VPC, IAM, ALB, RDS)
- ❌ Slower iteration for solo founder
- ⚠️ Planned for Phase 2 when scaling beyond free tier

### Fly.io
- ✅ Global edge, great CLI
- ❌ Less integrated managed PostgreSQL
- ❌ Slightly higher cost for same resources

### Self-Managed Kubernetes
- ✅ Maximum flexibility
- ❌ Massive operational overhead
- ❌ Overkill for single-service app

### Railway
- ✅ Similar to Render
- ❌ Less mature health check and metrics UI
- ❌ Chosen Render for superior PostgreSQL integration

## References
- OMNIAI Core Dockerfile: [`Dockerfile`](https://github.com/ahooTech/omniai-core)
- GitHub Actions Workflow: [`.github/workflows/ci.yml`](https://github.com/ahooTech/omniai-core/actions)
- Render Deployment: https://omniai-web.onrender.com
- Render PostgreSQL: Managed DB with auto-backups
- Structured Logging: [`src/omniai/core/logging.py`](https://github.com/ahooTech/omniai-core)
```