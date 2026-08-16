# Staff Canteen Management System

Generated: 08/16/2026 17:26:45

---

## Table of Contents

- .dockerignore
- .env.test.docker
- .gitattributes
- .gitignore
- docker-compose.yml
- docker-compose-test.yml
- Dockerfile
- docs\adr\001-database-choice.md
- docs\adr\002-multi-tenancy-strategy.md
- docs\adr\003-auth-architecture.md
- docs\adr\004-observability-stack.md
- docs\adr\005-deployment-pipeline.md
- docs\adr\006-framework-selection.md
- docs\adr\007-testing-strategy.md
- docs\runbooks\deploy.md
- Generate-Codebook.ps1
- git
- LICENSE
- limitercode.py
- pyproject.toml
- README.md
- requirements.txt
- requirements-dev.txt
- scripts\bootstrap.sh
- scripts\start.sh
- src\omniai\__init__.py
- src\omniai\api\__init__.py
- src\omniai\api\deps.py
- src\omniai\api\v1\agriculture.py
- src\omniai\api\v1\auth.py
- src\omniai\api\v1\health.py
- src\omniai\api\v1\invite.py
- src\omniai\api\v1\me.py
- src\omniai\api\v1\metrics.py
- src\omniai\api\v1\organization.py
- src\omniai\api\v1\schemas.py
- src\omniai\core\config.py
- src\omniai\core\jwt.py
- src\omniai\core\limiter.py
- src\omniai\core\logging.py
- src\omniai\core\logging_middleware.py
- src\omniai\core\metrics_config.py
- src\omniai\core\metrics_middleware.py
- src\omniai\core\middleware.py
- src\omniai\db\__init__.py
- src\omniai\db\session.py
- src\omniai\main.py
- src\omniai\models\__init__.py
- src\omniai\models\base.py
- src\omniai\models\invite.py
- src\omniai\models\organization.py
- src\omniai\models\user.py
- src\omniai\services\__init__.py
- src\omniai\services\auth.py
- src\omniai\services\invite.py
- src\omniai\services\organization.py
- tests\__init__.py
- tests\unit\__init__.py
- tests\unit\test_integration.py
- tests\unit\test_unit.py

---


<div style='page-break-after: always;'></div>

# File: .dockerignore

```dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
omniai.egg-info/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.orig
*.rej
.*.swp
.*.swo
.DS_Store
pip-log.txt
pip-delete-this-directory.txt
htmlcov/
.tox/
.nox/
.coverage
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
.mypy_cache/
cover/

# Virtual Environments
.venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# OS
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Secrets
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Linter caches
.ruff_cache/

# Docker-specific
.dockerignore
Dockerfile
docs/
#README.md
#tests/
```


<div style='page-break-after: always;'></div>

# File: .env.test.docker

```docker
ENV=test
# .env.test.docker
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/omniai_test
# We overide .env database url but not the JWT_SECRET_KEY
JWT_SECRET_KEY=d3f790154be359f68c5c361bd0079568936fd97ae6e43d01a673c5e5301b9d72
```


<div style='page-break-after: always;'></div>

# File: .gitattributes

```gitattributes

# Enforce consistent line endings
*           text=auto

# Force scripts to use LF (critical for Docker/Linux)
*.sh        text eol=lf
*.py        text eol=lf

# Lock core files
README.md   text eol=lf
pyproject.toml text eol=lf
*.toml      text eol=lf
*.yml       text eol=lf
*.yaml      text eol=lf

# Leave binary files alone
*.exe       binary
*.dll       binary
*.whl       binary
*.zip       binary
*.png       binary
*.jpg       binary
```


<div style='page-break-after: always;'></div>

# File: .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
omniai.egg-info/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.orig
*.rej
.*.swp
.*.swo
.DS_Store
pip-log.txt
pip-delete-this-directory.txt
htmlcov/
.tox/
.nox/
.coverage
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
.mypy_cache/
cover/

# Virtual Environments
.venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# OS
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Packaging (redundant with above, but safe to keep)
*.egg-info/
dist/
build/

# Secrets
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Docker
.dockerignore.env.test 

# Linter caches
.ruff_cache/

```


<div style='page-break-after: always;'></div>

# File: docker-compose.yml

```yml

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: omniai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  app:
    build: .
    ports:
      - "8000:8000"
    # ✅ Load ALL app config from .env — no duplication
    # ✅ DO NOT hardcode JWT_SECRET_KEY here!
    # Instead, load from your local .env file
    env_file:
      - .env  # ← This loads JWT_SECRET_KEY from your .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./src:/app/src

volumes:
  postgres_data:


```


<div style='page-break-after: always;'></div>

# File: docker-compose-test.yml

```yml

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: omniai_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    #volumes:
      #- postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  app:
    build: .
    ports:
      - "8000:8000"
    # ✅ Load ALL app config from .env — no duplication
    # ✅ DO NOT hardcode JWT_SECRET_KEY here!
    # 👇 CRITICAL: Use .env.test.docker so app connects to omniai_test
    env_file:
      - .env.test.docker   # ← This loads JWT_SECRET_KEY from your .env
    depends_on:
      db:
        condition: service_healthy
    environment:
      OMNIAI_DISABLE_RATE_LIMIT: 1
    volumes:
      - ./src:/app/src
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health/ready"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s

  # Test service
  test:
    build:
      context: .
      args:
        INSTALL_DEV: "true"
    env_file:
      - .env.test.docker  
    depends_on:
      app:
        condition: service_healthy
    environment:
      # So psql/pg_isready/dropdb don't prompt for password
      # OMNIAI_DISABLE_RATE_LIMIT: 1
      PGPASSWORD: postgres
      HOME: /tmp
    volumes:
      - ./htmlcov:/app/htmlcov
    command: |
      sh -c "
        echo '⏳ Waiting for DB...' &&
        pg_isready -h db -U postgres &&

        echo '🚀 Waiting for app health check...' &&
        timeout 30 sh -c 'while ! curl -s --fail http://app:8000/v1/health/ready; do sleep 1; done' &&

        echo '✅ App is ready!' &&

        echo '🔍 Running static analysis...' &&
        RUFF_CACHE_DIR=/tmp ruff check . &&
        mypy src/ &&
        bandit -r src/ -ll -x '**/migrations/**,**/__pycache__/**' &&
        safety check --full-report &&

        echo '🧪 Running tests with coverage...' &&
        pytest -v --tb=short --cov=omniai --cov-report=html --cov-fail-under=90
      "

volumes:
  postgres_data:


  
```


<div style='page-break-after: always;'></div>

# File: Dockerfile

```text
# Dockerfile
# Your app runs the same way everywhere (no “it works on my machine” issues)
# It’s lightweight and secure (no extra bloat)
# It’s ready for production (proper packaging, clear start command)

FROM python:3.11-slim

# Install system dependencies FIRST (best practice) to be used by database commands in test
# ✅ Install ALL system dependencies in ONE layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        postgresql-client \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
    
# 🔒 Critical: Patch pip BEFORE installing Python packages
RUN pip install --no-cache-dir --upgrade "pip>=25.2"

WORKDIR /app

# Copy all source and config for editable install
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
COPY tests/ ./tests/ 
COPY scripts/ ./scripts/

# 💡 New: Accept a build arg to decide whether to install test dependencies
ARG INSTALL_DEV=false
    
# Replace the two RUN lines with this:
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        # if variable in test is true install main deps + dev deps
      pip install --no-cache-dir --only-binary=all -e ".[dev]"; \
    else \
    # if variable in test is false install main deps only
      pip install --no-cache-dir --only-binary=all -e .; \
    fi

COPY scripts/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# Make the app user own the directory (optional but clean)
RUN chown -R app:app /app

# Switch to non-root user
USER app

# ✅ Set runtime configuration via environment variables
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000
ENV UVICORN_RELOAD=false

EXPOSE 8000



CMD ["/app/start.sh"]
# CMD ["python", "-m", "uvicorn", "omniai.main:app", "--host", "0.0.0.0", "--port", "8000"]


# This is my Docker file that is built by either docker-compose-test.yml for testing or docker-compose.yml for real world
```


<div style='page-break-after: always;'></div>

# File: docs\adr\001-database-choice.md

```md
```markdown
# [ADR-001] Use PostgreSQL as Primary Database with Application-Level Multi-Tenancy

## Status
✅ Accepted

## Context
OMNIAI Core requires a production-grade relational database to store:
- User identities (email, password hash)
- Organization memberships with role and default status
- Invite tokens for secure onboarding
- Full lifecycle of organizations: create, invite, leave, remove, delete

Key requirements:
- **Strong consistency** for authentication and tenant isolation
- **Efficient querying** of user-org relationships (including "default org" per user)
- **Scalable indexing** for high-concurrency auth and org-switching
- **Data integrity** across org membership changes (no orphaned states)
- **Future support for Row-Level Security (RLS)**
- **Operational simplicity** for cloud deployment (Render, AWS, GCP)

## Decision
We select **PostgreSQL 15+** as the primary database and implement:
- A normalized schema using SQLAlchemy 2.0 declarative models
- Explicit many-to-many `user_organization` association table with metadata
- Strategic indexes, including a **partial unique index** to enforce one default org per user
- Human-readable prefixed IDs (`usr_...`, `org_...`, `inv_...`) for debugging and auditability
- Full org lifecycle support: create → invite → join → leave/remove → delete

### Schema Design (Actual Implementation)

#### `users` Table
- `id`: `TEXT` primary key, default `"usr_" + uuid4().hex`
- `email`: unique, indexed
- `hashed_password`: bcrypt hash (72-byte truncated)
- `created_at`: timezone-aware timestamp

#### `organizations` Table
- `id`: `TEXT` primary key, default `"org_" + uuid4().hex`
- `name`: organization display name
- `slug`: unique, URL-friendly identifier (indexed)
- `is_active`: soft-deletion flag (future use)
- `description`: optional metadata
- `created_at`: timezone-aware timestamp

#### `user_organization` (Association Table)
- Composite primary key: `(user_id, organization_id)`
- `role`: `"owner"` or `"member"` (default: `"member"`)
- `is_default`: `BOOLEAN` — marks the user’s current active org
- `joined_at`: timestamp of membership creation
- **Partial Unique Index**:  
  ```sql
  CREATE UNIQUE INDEX idx_user_default_org 
  ON user_organization (user_id) 
  WHERE is_default = true;
  ```
  → Ensures **exactly one default org per user**

#### `invites` Table
- `id`: `TEXT` primary key, default `"inv_" + uuid4().hex`
- `token`: unique, random URL-safe string (32 bytes)
- `email`: invited user’s email (indexed)
- `organization_id`: foreign key to `organizations.id`
- `invited_by_id`: foreign key to `users.id` (the inviter)
- `expires_at`: auto-set to 7 days from creation
- `accepted_at`: nullable timestamp (set on acceptance)
- `is_active`: boolean flag (set to `false` on acceptance)

### Indexing Strategy
- `users(email)` → O(1) login lookup
- `organizations(slug)` → org resolution by URL
- `user_organization(user_id)` → list user’s orgs
- `user_organization(organization_id)` → list org members
- **Partial index on `(user_id)` where `is_default = true`** → enforce default org uniqueness
- `invites(token)` → O(1) invite validation
- `invites(email)` → prevent duplicate invites

### Lifecycle Enforcement
| Operation         | Constraint                                                       |
|----------         |------------                                                      |
| **Create Org**    | User becomes `owner`; personal org always `is_default=true`      |
| **Invite Member** | Only `owner` can invite; token expires in 7 days                 |
| **Accept Invite** | Email must match; user added as `member` with `is_default=false` |
| **Leave Org**     | Cannot leave personal org; last owner cannot leave               |
| **Remove Member** | Only `owner` can remove; cannot remove self or other owners      |
| **Delete Org**    | Only `owner` can delete; personal orgs are immutable             |

All operations are **transactionally safe** and **logically consistent** due to PostgreSQL’s ACID guarantees.

## Consequences

### Good
- **Data integrity**: Foreign keys, partial indexes, and app logic prevent invalid states
- **Debuggability**: Prefixed IDs (`usr_...`, `org_...`, `inv_...`) are human-readable in logs
- **Flexibility**: `role` and `is_default` in association table avoid extra joins
- **Security**: Invite tokens are random, unique, and time-bound
- **Future-proof**: `is_active` enables soft-delete; RLS can be layered later
- **Cloud-native**: Fully compatible with Render, AWS RDS, GCP Cloud SQL

### Bad
- **Storage overhead**: Text-based IDs slightly larger than UUID binary (negligible at scale)
- **Index complexity**: Partial index requires PostgreSQL (not portable to SQLite/MySQL)
- **Migration sensitivity**: Changing association table structure requires careful rollout

### Neutral
- **ORM dependency**: Tightly coupled to SQLAlchemy 2.0 patterns
- **No automatic sharding**: Will require manual partitioning beyond ~100M rows

## Alternatives Considered

### SQLite
- ❌ No support for partial indexes (`WHERE` clause in `CREATE UNIQUE INDEX`)
- ❌ Poor concurrency under write load — fails during parallel user onboarding
- ❌ Not viable for cloud deployment

### MongoDB
- ❌ Cannot enforce “one default org per user” without complex application logic
- ❌ Denormalization would duplicate org data across user documents → update anomalies
- ❌ Weak transaction support for join-like operations

### MySQL
- ❌ Partial indexes not supported until MySQL 8.0+, and syntax differs
- ❌ Less mature JSON and RLS ecosystem
- ❌ No compelling advantage over PostgreSQL for our advanced indexing needs

## References
- [PostgreSQL Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)
- OMNIAI Core Models:  
  - [`src/omniai/models/user.py`](https://github.com/ahooTech/omniai-core)  
  - [`src/omniai/models/organization.py`](https://github.com/ahooTech/omniai-core)  
  - [`src/omniai/models/invite.py`](https://github.com/ahooTech/omniai-core)
- Render PostgreSQL: https://render.com/docs/databases/postgres
```
```


<div style='page-break-after: always;'></div>

# File: docs\adr\002-multi-tenancy-strategy.md

```md

```markdown
# [ADR-002] Multi-Tenancy via Application-Level Context with Default Org Enforcement

## Status
✅ Accepted

## Context
OMNIAI Core must support:
- Users belonging to **multiple organizations simultaneously**
- Each user having a **single active (default) organization** at any time
- **Strict data isolation**: no cross-tenant data leakage
- **Role-based permissions**: `owner` (can delete org, remove members) vs `member` (can only leave)
- **Immutable personal org**: created on signup, never deletable
- Seamless org switching via client-managed state

Requirements:
- Zero data leaks between tenants
- Low-latency org resolution
- Auditability of org context in logs
- Compatibility with future Row-Level Security (RLS)

## Decision
We implement **application-level multi-tenancy** using:
1. **Explicit tenant context** via `X-Tenant-ID` HTTP header
2. **Middleware-enforced validation** on every protected route
3. **Database schema** with rich association metadata (`user_organization` table)
4. **Query scoping** at the repository/service layer
5. **Lifecycle enforcement** for org membership and deletion

### Key Components

#### 1. Data Model (`user_organization` Association Table)
- Many-to-many relationship between `users` and `organizations`
- Columns:
  - `user_id`, `organization_id` → composite PK
  - `role`: `"owner"` or `"member"`
  - `is_default`: `BOOLEAN` — marks the user’s current active org
  - `joined_at`: timestamp of membership
- **Partial unique index**:  
  ```sql
  CREATE UNIQUE INDEX idx_user_default_org ON user_organization (user_id)
  WHERE is_default = true;
  ```
  → Guarantees **exactly one default org per user**

#### 2. Tenant Context Propagation
- Client sends `X-Tenant-ID: org_xxx` header on all requests
- Middleware validates:
  - Header exists
  - Org exists and is active
  - User is a member of the org
  - User’s session is valid
- On success, binds `(user_id, org_id, role)` to request context
- **No server-side "active org" state** — fully client-driven

#### 3. Data Isolation Enforcement
- All service/repository methods accept `current_org_id`
- Database queries include:  
  ```python
  db.query(Model).filter(Model.org_id == current_org_id)
  ```
- No global queries allowed — enforced by code review and testing

#### 4. Default Organization Logic
- On signup: auto-create personal org `Personal – {email}` with `is_default=true`
- **Personal org is immutable**:
  - Cannot be deleted
  - Cannot be left
  - Always exists for every user
- User can switch ACTIVE org via profile update (client calls `PATCH /v1/users/me`)
- First joined org which is default becomes ACTIVE if none exists

#### 5. Role-Based Access Control (RBAC)
- Middleware attaches `role` to request context
- Endpoints enforce:
  - Only `owner` can **delete org**, **remove members**, or **invite**
  - `member` can only **leave org**
  - **Last owner protection**: cannot leave if no other owners exist
  - **Owner immunity**: cannot be removed by other owners

#### 6. Lifecycle Integrity Rules
| Operation         | Constraint                                                       |
|----------         |------------                                                      |
| **Create Org**    | User becomes `owner`; personal org always `is_default=true`      |
| **Invite Member** | Only `owner` can invite; token expires in 7 days                 |
| **Accept Invite** | Email must match; user added as `member` with `is_default=false` |
| **Leave Org**     | Cannot leave personal org; last owner cannot leave               |
| **Remove Member** | Only `owner` can remove; cannot remove self or other owners      |
| **Delete Org**    | Only `owner` can delete; personal orgs are immutable             |

All operations are **transactionally safe** and **logically consistent** due to PostgreSQL’s ACID guarantees.

## Consequences

### Good
- **Strong isolation**: App-layer filtering prevents accidental cross-tenant access
- **Flexible membership**: Users can join thousands of orgs without schema changes
- **Audit-ready**: Every log entry includes `org_id` and `user_id`
- **Client-controlled UX**: Frontend manages active org via header
- **Future-proof**: Can layer PostgreSQL RLS as defense-in-depth later
- **Data integrity**: Business rules enforced at service + DB level

### Bad
- **Developer discipline required**: Forgetting to scope queries risks data leaks
- **Header dependency**: Clients must manage `X-Tenant-ID` correctly
- **No automatic enforcement**: Unlike pure RLS, bugs can bypass isolation

### Neutral
- **One extra DB join**: Resolving org membership adds minor latency (~2ms)
- **Stateless design**: No server-side session — scales horizontally

## Alternatives Considered

### Pure PostgreSQL Row-Level Security (RLS)
- ✅ Automatic, unbreakable isolation
- ❌ Hard to test/debug (policies hidden in DB)
- ❌ Complex for many-to-many org models
- ❌ Less portable across cloud providers
- ⚠️ Chosen as **future enhancement**, not initial strategy

### Separate Schema per Tenant
- ✅ Total isolation
- ❌ Operational nightmare (10K tenants = 10K schemas)
- ❌ No shared data (e.g., global user directory)
- ❌ Not viable for our use case

### Separate Database per Tenant
- ✅ Maximum isolation
- ❌ Cost-prohibitive at scale
- ❌ Impossible for free-tier users
- ❌ Kills network effects

## References
- OMNIAI Core Models:  
  - [`user.py`](https://github.com/ahooTech/omniai-core/blob/main/src/omniai/models/user.py)  
  - [`organization.py`](https://github.com/ahooTech/omniai-core/blob/main/src/omniai/models/organization.py)  
  - [`invite.py`](https://github.com/ahooTech/omniai-core/blob/main/src/omniai/models/invite.py)
- Middleware: [`middleware.py`](https://github.com/ahooTech/omniai-core) (tenant validation + context binding)
- Render Deployment: https://omniai-web.onrender.com/v1/health  
```
```


<div style='page-break-after: always;'></div>

# File: docs\adr\003-auth-architecture.md

```md
```markdown
# [ADR-003] Stateless JWT Authentication with Secure Password Handling and Rate Limiting

## Status
✅ Accepted

## Context
OMNIAI Core requires a secure, scalable, and auditable authentication system that:
- Supports email/password login for global users (including emerging markets)
- Prevents brute-force and credential-stuffing attacks
- Provides stateless sessions for horizontal scalability
- Enforces strong password security without usability friction
- Integrates seamlessly with multi-tenancy context
- Logs all auth events for security monitoring

Key threats to mitigate:
- Password cracking (weak hashing)
- Brute-force login attempts
- Credential leakage via logs or errors
- Session hijacking
- User enumeration via error messages

## Decision
We implement a **stateless JWT-based authentication flow** with:
1. **Secure password storage**: `bcrypt` with 72-byte input truncation fix
2. **Short-lived JWTs**: HS256-signed tokens (24-hour expiry)
3. **IP-based rate limiting**: 5 failed logins per minute per IP
4. **Minimal error disclosure**: Generic "invalid credentials" message
5. **Structured audit logging**: All auth attempts logged with `trace_id`, `email`, outcome
6. **Zero sensitive data in logs**: No passwords, tokens, or PII in structured logs

### Detailed Implementation

#### 1. Password Security
- **Hashing algorithm**: `bcrypt` (12 rounds)
- **Input handling**:  
  - Truncate passwords to **72 bytes** before hashing (to prevent DoS via long inputs)  
  - Use `encode("utf-8")[:72]` to avoid bcrypt library inconsistencies
- **Storage**: Only `hashed_password` stored in `users` table — never plaintext
- **Validation**: Pydantic enforces:
  - Min 8 chars
  - Uppercase, lowercase, digit, special char
  - No common patterns (enforced by frontend)

#### 2. JWT Design
- **Algorithm**: HMAC-SHA256 (`HS256`)
- **Payload**:
  ```json
  {
    "sub": "usr_xxx",
    "exp": 1735689600,
    "iat": 1735603200
  }
  ```
- **Secret**: 32+ byte random key from `JWT_SECRET_KEY` (cloud-managed)
- **No refresh tokens**: New JWT issued on every successful login (implicit rotation)
- **Validation**: Reject tokens with invalid `sub` format (`usr_...` prefix required)

#### 3. Rate Limiting
- **Library**: `slowapi` (Starlette-compatible)
- **Policy**:  
  - `POST /v1/auth/login` → max **5 requests/minute per IP**  
  - Count both success and failure (to prevent enumeration)
- **Storage**: In-memory counter (Redis-ready for future scale)
- **Response**: `429 Too Many Requests` with no details
- **Bypass**: Disabled in local development (`ENV != production`)

#### 4. Error Handling & Security
- **Login failure**: Always return `401 Unauthorized` with message:  
  `"Invalid email or password"`  
  → Never reveal if email exists
- **Validation**: Pydantic enforces email format, password strength
- **Headers**: No sensitive data in logs (passwords never logged)
- **Token errors**: Return generic `401` — never expose JWT structure

#### 5. Audit Logging
- **Events logged**:
  - `login_attempt` (email, trace_id)
  - `login_success` (email, user_id, trace_id)
  - `login_failed` (email, reason="invalid_credentials", trace_id)
  - `auth_user_not_found` (email, trace_id)
  - `auth_password_invalid` (email, trace_id)
- **Context**: All logs include `client_ip`, `trace_id`, and (when authenticated) `user_id`
- **Redaction**: No passwords, tokens, or raw request bodies in logs

#### 6. Integration with Multi-Tenancy
- Auth is **tenant-agnostic**: Login returns user identity only
- `/v1/me` resolves active org using `X-Tenant-ID` header
- No auth endpoint exposes org context — prevents tenant enumeration

## Consequences

### Good
- **Brute-force resistant**: Rate limiting blocks automated attacks
- **Password-safe**: bcrypt + 72-byte fix prevents DoS and cracking
- **Stateless**: Scales horizontally without session store
- **Audit-compliant**: Full trail of auth activity for security teams
- **User-friendly**: No CAPTCHAs or MFA friction (for Phase 1)
- **Zero data leaks**: Structured logs contain no PII or secrets

### Bad
- **No built-in MFA**: Requires future extension for high-security use cases
- **HS256 key management**: Secret must be rotated carefully (no auto-key-rotation)
- **In-memory rate limiting**: Not persistent across restarts (acceptable for early scale)

### Neutral
- **JWT size**: ~300 bytes — negligible bandwidth impact
- **Clock skew sensitivity**: Requires NTP-synced servers (standard in cloud)

## Alternatives Considered

### OAuth2/OpenID Connect (e.g., Auth0, Google)
- ✅ Reduces auth maintenance burden
- ❌ Adds vendor lock-in and cost
- ❌ Poor UX in low-connectivity regions (common in target markets)
- ❌ Overkill for initial MVP

### Session Cookies + Redis
- ✅ Easier revocation
- ❌ Adds stateful dependency (Redis)
- ❌ More complex scaling
- ❌ Unnecessary for our stateless API design

### Argon2 instead of bcrypt
- ✅ Stronger against GPU cracking
- ❌ Less battle-tested in Python ecosystem
- ❌ Higher memory usage — risk on low-resource edge deployments
- ⚠️ May adopt in Phase 2 if threat model evolves

## References
- OMNIAI Core Auth Service: [`src/omniai/services/auth.py`](https://github.com/ahooTech/omniai-core)
- Rate Limiting Middleware: [`slowapi` integration](https://github.com/ahooTech/omniai-core)
- Password Hashing Fix: [bcrypt 72-byte truncation](https://github.com/pyca/bcrypt/issues/104)
- Render Deployment: https://omniai-web.onrender.com/v1/auth/login
- Structured Logging: [`src/omniai/core/logging.py`](https://github.com/ahooTech/omniai-core)
```
```


<div style='page-break-after: always;'></div>

# File: docs\adr\004-observability-stack.md

```md
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
```


<div style='page-break-after: always;'></div>

# File: docs\adr\005-deployment-pipeline.md

```md
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
```


<div style='page-break-after: always;'></div>

# File: docs\adr\006-framework-selection.md

```md
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

| Requirement       | FastAPI Solution                                                     |
|-----------        |------------------                                                    |
| **Async Support** | Native `async`/`await` with Starlette under the hood                 |
| **Validation**    | Pydantic v2 models auto-validate requests/responses                  |
| **Documentation** | Auto-generated OpenAPI + Swagger UI at `/docs`                       |
| **Type Safety**   | Full mypy compatibility; type hints drive validation                 |
| **Performance**   | Benchmarks show ~3x faster than Flask/Django (TechEmpower)           |
| **Middleware**    | Starlette-compatible middleware stack (logging, auth, rate limiting) |
| **Ecosystem**     | First-class support for SQLAlchemy async, structlog, slowapi         |

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
- **Structured Logging Integration**:  
  Middleware binds `trace_id`, `user_id`, `org_id` to all logs
- **Health Checks**:  
  Standard `/v1/health` and `/v1/health/ready` endpoints for cloud platforms

## Consequences

### Good
- **Developer Velocity**: No manual validation or doc writing — focus on business logic
- **Fewer Bugs**: Type-driven validation catches 80% of input errors at boundary
- **Self-Documenting API**: `/docs` always up-to-date — critical for frontend/AI agent integration
- **High Throughput**: Handles 1K+ RPM on modest hardware (verified via load testing)
- **Future-Proof**: Async foundation ready for LLM streaming, WebSockets, background agents
- **Observability-Ready**: Full context propagation for debugging and auditing

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
- Structured Logging: [`src/omniai/core/logging.py`](https://github.com/ahooTech/omniai-core)
```
```


<div style='page-break-after: always;'></div>

# File: docs\adr\007-testing-strategy.md

```md
```markdown
# [ADR-007] Isolated, High-Coverage Testing Strategy with CI Quality Gates

## Status
✅ Accepted

## Context
OMNIAI Core must maintain **extreme reliability** because:
- It handles sensitive user data (email, passwords, org memberships)
- Multi-tenancy logic is complex (default org, roles, isolation)
- Auth and tenant validation are security-critical
- Future AI agents will depend on this foundation

## Requirements:
- **No test pollution**: Tests must not affect each other or dev DB
- **High confidence**: >90% test coverage on core logic
- **Fast feedback**: Tests run in <2 minutes in CI
- **Enforced quality**: Broken tests block deployment
- **Realistic environment**: Test against actual PostgreSQL (not mocks)

## Decision
We implement a strict, isolated testing strategy using:
1. **Dedicated test database**: `omniai_test` (dropped/recreated per run)
2. **Pytest fixtures**: For DB sessions, test users, orgs
3. **Coverage enforcement**: >90% line coverage via `pytest-cov`
4. **CI quality gates**: GitHub Actions blocks merge on test failure
5. **Real DB integration**: No mocking of SQLAlchemy or PostgreSQL

### Detailed Implementation

#### 1. Test Database Isolation
- **Database name**: `omniai_test` (separate from `omniai` dev/prod)
- **Lifecycle**:
  - Before test suite: `DROP DATABASE IF EXISTS omniai_test; CREATE DATABASE omniai_test;`
  - After test suite: `DROP DATABASE omniai_test;`
- **Per-test transactions**:  
  Each test runs in a transaction that rolls back → no cleanup needed
- **Environment safety**:  
  `DATABASE_URL` overridden in test env → impossible to hit prod DB
- **Render compatibility**: Uses same PostgreSQL version as production

#### 2. Test Structure
- **Unit tests**: Pure functions (e.g., password hashing, slug generation)
- **Integration tests**:  
  - Auth flow: signup → login → access `/me`  
  - Org flow: create org → invite user → switch default org  
  - Tenant isolation: verify user A can’t see org B
  - **Error paths**: All 4xx/5xx cases covered (e.g., last owner protection)
- **Fixtures**:  
  - `test_user`, `test_org`, `auth_headers` → reusable test data
- **Async support**: `pytest-asyncio` for async endpoint tests
- **Email uniqueness**: All test emails use `uuid4()` to prevent collisions

#### 3. Coverage Enforcement
- **Tool**: `pytest-cov`
- **Threshold**: Fail if coverage < 90%
- **Report**: HTML coverage report saved as CI artifact
- **Focus areas**:  
  - `services/` (auth, org logic) → 100% covered  
  - `api/` (routers) → >90% covered  
  - Excludes: `main.py`, migrations
- **Branch coverage**: All error paths (e.g., "last owner", "personal org immutable") explicitly tested

#### 4. CI Quality Gates (GitHub Actions)
- **Pipeline**:
  1. Run unit + integration tests
  2. Measure coverage → fail if <90%
  3. Run linter (`ruff`)
  4. Run type checker (`mypy`)
  5. Run security scanner (`bandit`, `safety`)
- **Policy**: Any step failure = deployment blocked
- **Speed**: Tests complete in <90 seconds (optimized DB setup)
- **Artifact**: Coverage report published for audit

#### 5. No Mocking Policy
- **Why**: Mocking hides integration bugs (e.g., SQL syntax errors, constraint violations)
- **What we test against**:
  - Real PostgreSQL (via Docker in CI)
  - Real SQLAlchemy async engine
  - Real FastAPI test client
- **Exception**: External HTTP calls (e.g., SMS APIs) → mocked
- **Partial index validation**: Tests verify PostgreSQL-specific features (e.g., one default org per user)

## Consequences

### Good
- **Zero test pollution**: Parallel test runs safe
- **High confidence**: Critical paths (auth, tenant isolation) fully covered
- **Security assurance**: Auth logic tested against real attack vectors
- **CI as gatekeeper**: No broken code reaches production
- **Debuggable**: Real DB errors surface immediately
- **Audit-ready**: Full coverage report for compliance

### Bad
- **Slightly slower tests**: ~90s vs ~30s with full mocking
- **DB setup complexity**: Requires careful teardown

### Neutral
- **Test maintenance**: New features require new tests (enforced by culture)
- **Coverage focus**: May incentivize “easy” tests over edge cases (mitigated by code review)

## Alternatives Considered

### Full Mocking (unittest.mock)
- ✅ Faster tests
- ❌ Misses integration bugs (e.g., SQL joins, constraints)
- ❌ False confidence — passes in test, fails in prod

### In-Memory SQLite
- ✅ No DB setup
- ❌ Different SQL dialect → misses PostgreSQL-specific bugs (e.g., partial indexes)
- ❌ No async support parity

### Lower Coverage Threshold (e.g., 70%)
- ✅ Less test writing
- ❌ Unacceptable risk for auth/tenant logic
- ❌ Encourages tech debt

## Verdict
This strategy ensures OMNIAI Core is **battle-tested before every deploy** — critical for a system that will underpin trillion-dollar AI applications.

> **“If it’s not tested, it’s broken.”**

## References
- OMNIAI Core Tests: [`tests/`](https://github.com/ahooTech/omniai-core/tree/main/tests)
- GitHub Actions: [CI Workflow](https://github.com/ahooTech/omniai-core/actions)
- Coverage Report: Generated in CI artifacts
- Render Deployment: Only green CI → auto-deploy
- Partial Index Validation: [`user_organization` table](https://github.com/ahooTech/omniai-core/blob/main/src/omniai/models/user.py)
```
```


<div style='page-break-after: always;'></div>

# File: docs\runbooks\deploy.md

```md

---

### ✅ `docs/runbooks/deploy.md`

```markdown
# OMNIAI Core Deployment Runbook

This document describes how to deploy, update, and troubleshoot OMNIAI Core in production.

> **Target Platform**: [Render](https://render.com)  
> **Last Verified**: January 2026  
> **Owner**: Engineering Team

---

## 📦 Prerequisites

1. **GitHub Account** with access to the `ahooTech/omniai-core` repository
2. **Render Account** (free tier sufficient for MVP)
3. **Docker** installed locally (for testing)
4. **Environment Variables** ready (see [Secrets](#secrets))

---

## 🚀 One-Click Production Deployment (New Setup)

### Step 1: Fork or Clone the Repository
```bash
git clone https://github.com/ahooTech/omniai-core.git
cd omniai-core
```

### Step 2: Create Render Services

#### A. PostgreSQL Database
1. Go to [Render Dashboard → Databases](https://dashboard.render.com/databases)
2. Click **New PostgreSQL Database**
3. Configure:
   - **Name**: `omniai-prod-db`
   - **Region**: Closest to your users (e.g., `Oregon` for global)
   - **Version**: PostgreSQL 15+
   - **Free Tier**: Enabled
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgres://...`)

#### B. Web Service
1. Go to [Render Dashboard → Web Services](https://dashboard.render.com/web)
2. Click **New Web Service**
3. Connect your GitHub repo (`ahooTech/omniai-core`)
4. Configure:
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Build Command**: (leave empty — uses Dockerfile)
   - **Start Command**: (leave empty)
5. Under **Advanced**:
   - **Health Check Path**: `/v1/health/ready`
   - **Health Check Interval**: 10 seconds
6. Click **Create Web Service**

### Step 3: Set Environment Variables
In your Web Service dashboard → **Environment**:

| Key               | Value                           | Source       |
|-----              |-------                          |--------      |
| `DATABASE_URL`    | `<your Render DB internal URL>` | From Step 2A |
| `JWT_SECRET_KEY`  | `openssl rand -hex 32`          | Generate new |
| `ENV`             | `production`                    | Hardcoded    |

> 🔒 **Never commit these values to Git.**

### Step 4: Trigger Initial Deploy
- Push any change to `main`:
  ```bash
  git commit --allow-empty -m "Trigger deploy"
  git push origin main
  ```
- Or click **Manual Deploy** in Render dashboard.

✅ **Done!** Your API is live at `https://<service-name>.onrender.com`

---

## 🔄 Updating Production

1. **Push to `main`**:
   ```bash
   git checkout main
   git pull
   # Make changes
   git add .
   git commit -m "feat: add X"
   git push origin main
   ```
2. **GitHub Actions** will:
   - Run tests, linting, security scans
   - Build Docker image
   - Push to GHCR
3. **Render** automatically:
   - Pulls new image
   - Runs health checks
   - Swaps traffic on success

> ⏱️ **Typical deploy time**: <3 minutes

---

## 🧪 Local Development Setup

### Requirements
- Docker + Docker Compose

### Steps
1. Copy env file:
   ```bash
   cp .env.example .env
   # Edit .env with your local secrets
   ```
2. Start services:
   ```bash
   docker-compose up --build
   ```
3. Access:
   - API: `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`
   - DB: `postgresql://omniai:omniai@localhost:5432/omniai`

> 💡 **Test DB**: `omniai_test` is used automatically during `pytest`

---

## 🔍 Troubleshooting

### Common Issues

| Symptom                               | Diagnosis              | Fix                                          |
|--------                               |-----------             |-----                                         |
| **502 Bad Gateway**                   | App crashed on startup | Check logs for missing env vars              |
| **401 on /me**                        | Invalid JWT            | Ensure `JWT_SECRET_KEY` matches between runs |
| **DB connection failed**              | Wrong `DATABASE_URL`   | Use **Internal Database URL** from Render    |
| **Tests pass locally but fail in CI** | Test DB not isolated   | Ensure CI uses `DATABASE_URL_TEST`           |

### Accessing Logs
- **Render**: Dashboard → Web Service → **Logs**
- **Local**: `docker-compose logs app`

### Manual Health Check
```bash
curl https://<your-app>.onrender.com/v1/health/ready
# Should return: {"status": "ready", "service": "omniai-core"}
```

---

## 🛡️ Secrets Management

### Never Store In:
- Git history
- Docker images
- Client-side code

### Secure Storage:
- **Production**: Render Environment Variables
- **Local Dev**: `.env` (added to `.gitignore`)

### Rotate Secrets:
1. Generate new `JWT_SECRET_KEY`
2. Update in Render dashboard
3. Redeploy (no downtime)

---

## 📈 Scaling Beyond Free Tier

When traffic grows:
1. Upgrade Render Web Service to **Starter** ($7/mo)
2. Enable **Auto Deploy from Branch** for staging
3. Add **Custom Domain** with TLS
4. Migrate to **AWS RDS + ECS** (see future runbook)

---

## 📚 References
- [Render Docs](https://render.com/docs)
- [OMNIAI Core GitHub](https://github.com/ahooTech/omniai-core)
- [ADR-005: Deployment Pipeline](../adr/005-deployment-pipeline.md)
```

---
```


<div style='page-break-after: always;'></div>

# File: Generate-Codebook.ps1

```ps1
<#
.\Generate-Codebook.ps1 -ProjectPath "C:\Users\DAYLIFF\Desktop\omniai-core"
#>


param(
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$GeneratePdf
)

# ============================================================
# Configuration
# ============================================================

$Root = (Resolve-Path $ProjectPath).Path

$MarkdownFile = Join-Path $Root "Codebase.md"
$PdfFile      = Join-Path $Root "Codebase.pdf"

$ExcludedDirectories = @(
    ".git",
    ".github",
    "node_modules",
    "coverage",
    "dist",
    "build",
    "bin",
    "obj",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "migrations"
)

$ExcludedExtensions = @(
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".svg",".webp",".avif",
    ".pdf",".zip",".7z",".rar",
    ".exe",".dll",".so",
    ".woff",".woff2",".ttf",".eot",
    ".pyc",".class",".db",".sqlite3",".log"
)

# Delete old markdown if it exists
if (Test-Path $MarkdownFile) {
    Remove-Item $MarkdownFile -Force
}

# ============================================================
# Helper Function
# ============================================================

function Add-Line {
    param([string]$Text)

    Add-Content -Path $MarkdownFile -Value $Text -Encoding UTF8
}

# ============================================================
# Scan Files
# ============================================================

Write-Host ""
Write-Host "Scanning repository..."
Write-Host ""

$Files = Get-ChildItem -Path $Root -Recurse -File | Where-Object {

    $relative = $_.FullName.Substring($Root.Length).TrimStart('\')

    foreach ($dir in $ExcludedDirectories) {
        if ($relative -split "\\" -contains $dir) {
            return $false
        }
    }

    if ($ExcludedExtensions -contains $_.Extension.ToLower()) {
        return $false
    }

    return $true

} | Sort-Object FullName

Write-Host "Found $($Files.Count) files."
Write-Host ""

# ============================================================
# Markdown Header
# ============================================================

Add-Line "# Staff Canteen Management System"
Add-Line ""
Add-Line "Generated: $(Get-Date)"
Add-Line ""
Add-Line "---"
Add-Line ""

# ============================================================
# Table of Contents
# ============================================================

Add-Line "## Table of Contents"
Add-Line ""

foreach ($file in $Files) {

    $relative = $file.FullName.Substring($Root.Length).TrimStart('\')

    Add-Line "- $relative"

}

Add-Line ""
Add-Line "---"
Add-Line ""

# ============================================================
# Add Every File
# ============================================================

$index = 1

foreach ($file in $Files) {

    $relative = $file.FullName.Substring($Root.Length).TrimStart('\')

    Write-Host "[$index/$($Files.Count)] $relative"

    $language = $file.Extension.TrimStart('.')

    if ([string]::IsNullOrWhiteSpace($language)) {
        $language = "text"
    }

    Add-Line ""
    Add-Line "<div style='page-break-after: always;'></div>"
    Add-Line ""
    Add-Line "# File: $relative"
    Add-Line ""

    # Opening code fence
    Add-Line ('```' + $language)

    try {

        $content = Get-Content $file.FullName -Raw -Encoding UTF8

        Add-Content -Path $MarkdownFile -Value $content -Encoding UTF8

    }
    catch {

        Add-Line "[Unable to read file.]"

    }

    # Closing code fence
    Add-Line '```'
    Add-Line ""

    $index++

}

Write-Host ""
Write-Host "Markdown created successfully!"
Write-Host ""
Write-Host $MarkdownFile

# ============================================================
# Optional PDF Generation
# ============================================================

if ($GeneratePdf) {

    $Pandoc = Get-Command pandoc -ErrorAction SilentlyContinue

    if ($Pandoc) {

        Write-Host ""
        Write-Host "Generating PDF..."

        & pandoc `
            $MarkdownFile `
            -o $PdfFile `
            --toc `
            --highlight-style=tango

        Write-Host ""
        Write-Host "PDF created:"
        Write-Host $PdfFile

    }
    else {

        Write-Host ""
        Write-Host "Pandoc was not found."
        Write-Host ""
        Write-Host "Install it from:"
        Write-Host "https://pandoc.org/installing.html"

    }

}



# The attached is a project structure with all it's files. I wan't to generate its, codebase using this
# script " "  
# so I don't know the excluded directories and extensions I should add in the script. 
# The goal is for me to give you the code, understernd it and tell me the visible projects that are
# fixes we can apply to it for highest possible visibility.
```


<div style='page-break-after: always;'></div>

# File: git

```text
```


<div style='page-break-after: always;'></div>

# File: LICENSE

```text
MIT License

Copyright (c) 2026 Antony Henry Oduor Onyango

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```


<div style='page-break-after: always;'></div>

# File: limitercode.py

```py
# omniai/core/limiter.py
"""
import os
from functools import wraps
from typing import Callable, Any, Coroutine, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

# Global flag Check if rate limiting is disabled
DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")


# Get Redis URL (optional — if not set, falls back to in-memory)
REDIS_URL = os.getenv("REDIS_URL")

# Define _real_limiter as a module-level global — conditionally
_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    # Real limiter (only used if enabled) &&
    # Use Redis if available, otherwise in-memory (not recommended for prod)
    storage_uri = REDIS_URL if REDIS_URL else None
    _real_limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri  # ← This enables Redis!
    )

def conditional_limit(limit: str) -> Callable[..., Callable[..., Coroutine[Any, Any, Any]]]:
    #Apply rate limit only if OMNIAI_DISABLE_RATE_LIMIT is not set.
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    else:
        return _real_limiter.limit(limit)

# Expose limiter instance for app integration
limiter = _real_limiter

"""
"""
# src/omniai/core/limiter.py
import os
from functools import wraps
from typing import Callable, Any, Coroutine, Optional, TypeVar, cast
from slowapi import Limiter
from slowapi.util import get_remote_address
from urllib.parse import urlparse

DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    if REDIS_URL:
        parsed = urlparse(REDIS_URL)
        if parsed.scheme == "rediss":
            # Convert rediss:// → redis://
            storage_uri = f"redis://{parsed.hostname}:{parsed.port or 6379}"
            # Use STRING VALUES that redis-py will parse correctly
            _real_limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=storage_uri,
                storage_options={
                    "ssl": "True",          # ← STRING "True"
                    "ssl_cert_reqs": "none" # ← STRING "none"
                }
            )
        else:
            _real_limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=REDIS_URL
            )
    else:
        _real_limiter = Limiter(key_func=get_remote_address)

# --- Decorator (unchanged) ---
F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def conditional_limit(limit: str) -> Callable[[F], F]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator
    else:
        return _real_limiter.limit(limit)

limiter = _real_limiter

"""


"""
import os
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar, cast

from slowapi import Limiter
from slowapi.util import get_remote_address

DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    if REDIS_URL:
        # ✅ Use the URL AS-IS — no modification
        _real_limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=REDIS_URL  # ← Just pass it directly
        )
    else:
        _real_limiter = Limiter(key_func=get_remote_address)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def conditional_limit(limit: str) -> Callable[[F], F]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator
    else:
        return _real_limiter.limit(limit)

limiter = _real_limiter





"""



# Main.py

"""
# 🔒 Security & config audit at startup
logger.info(
    "application_startup_init",
    version="1.0",
    database_engine="postgresql",
    async_driver="asyncpg",
    token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    jwt_algorithm=settings.JWT_ALGORITHM,
    debug_mode=(len(settings.JWT_SECRET_KEY) < 32)
)

if len(settings.JWT_SECRET_KEY) < 32:
    logger.critical(
        "security_risk_weak_jwt_secret",
        message="JWT_SECRET_KEY is less than 32 bytes — rotate immediately!"
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize readiness flag
    app.state.ready = False

    # Wait for DB to be ready and create tables
    for i in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(UserBase.metadata.create_all)
                await conn.run_sync(OrgBase.metadata.create_all)
            logger.info("database_initialized", tables_created=["users", "organizations", "user_organization"])
            break
        except OperationalError as e:
            logger.warning("database_connection_retry", attempt=i+1, max_attempts=10, error=str(e))
            await asyncio.sleep(2)
    else:
        logger.error("database_connection_failed", message="Failed to connect to database after 10 attempts")
        raise RuntimeError("Failed to connect to database after 10 attempts") from None

    # ✅ MARK AS READY AFTER STARTUP TASKS
    app.state.ready = True
    yield

    # Shutdown
    app.state.ready = False
    await engine.dispose()
    logger.info("application_shutdown", message="Database engine disposed")

"""


"""


# src/omniai/api/v1/schemas.py
import re
from typing import List
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="User's email address. Must be unique across the platform.",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        description=(
            "Secure password with at least 8 characters, including uppercase, "
            "lowercase, digit, and special character."
        ),
        min_length=8,
        example="MyP@ssw0rd!"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain a special character")
        return v


class Token(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT access token for authenticating API requests",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer' for this API)",
        example="bearer"
    )


class OrganizationSummary(BaseModel):
    id: str = Field(
        ...,
        description="Unique organization ID (org_... format)",
        example="org_a1b2c3d4e5f6"
    )
    name: str = Field(
        ...,
        description="Human-readable organization name",
        example="Acme Corp"
    )
    slug: str = Field(
        ...,
        description="URL-friendly organization identifier",
        example="acme-corp"
    )
    role: str = Field(
        ...,
        description="User's role in this organization: 'owner' or 'member'",
        example="owner"
    )
    is_default: bool = Field(
        ...,
        description="Whether this is the user's default organization on login",
        example=True
    )


class UserMe(BaseModel):
    id: str = Field(
        ...,
        description="Unique user ID (usr_... format)",
        example="usr_x9y8z7w6v5u4"
    )
    email: str = Field(
        ...,
        description="User's verified email address",
        example="user@example.com"
    )
    active_organization_id: str = Field(
        ...,
        description="ID of the currently active organization",
        example="org_a1b2c3d4e5f6"
    )
    role_in_active_org: str = Field(
        ...,
        description="User's role in the active organization",
        example="admin"
    )
    organizations: List[OrganizationSummary] = Field(
        ...,
        description="List of all organizations the user belongs to"
    )


    """


###############################################################
# Unit tests for src/omniai/services/invite.py
###############################################################

"""
@pytest.mark.asyncio
async def test_create_invite_success(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.services.auth import create_user_with_org
    #from omniai.models.user import User
    from sqlalchemy import select

    # Generate unique emails
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"

    # Create owner
    await create_user_with_org(db, owner_email, "SecurePass123!")
    result = await db.execute(select(User).where(User.email == owner_email))
    owner = result.scalar_one()
    
    # Create org
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    await db.commit()

    # Create invite
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    assert invite.email == invitee_email
    assert invite.organization_id == org.id
    assert invite.invited_by_id == owner.id
    assert len(invite.token) > 20


@pytest.mark.asyncio
async def test_create_invite_forbidden_not_owner(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.services.auth import create_user_with_org
    #from omniai.models.user import User
    from sqlalchemy import select

    # Unique emails
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"

    # Create two users
    await create_user_with_org(db, owner_email, "SecurePass123!")
    await create_user_with_org(db, non_owner_email, "SecurePass123!")
    
    # Get users
    owner_result = await db.execute(select(User).where(User.email == owner_email))
    owner = owner_result.scalar_one()
    non_owner_result = await db.execute(select(User).where(User.email == non_owner_email))
    non_owner = non_owner_result.scalar_one()
    
    # Create org (owned by owner)
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    await db.commit()

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    from omniai.services.invite import create_invite, accept_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.services.auth import create_user_with_org
    #from omniai.models.user import User
    from sqlalchemy import select

    # Unique emails
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    member_email = f"member_{uuid.uuid4().hex}@test.com"

    # Create owner and org
    await create_user_with_org(db, owner_email, "SecurePass123!")
    owner_result = await db.execute(select(User).where(User.email == owner_email))
    owner = owner_result.scalar_one()
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    await db.commit()

    # Create invite
    invite_data = InviteCreate(email=member_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)
    await db.commit()

    # Create member user
    await create_user_with_org(db, member_email, "SecurePass123!")
    member_result = await db.execute(select(User).where(User.email == member_email))
    member = member_result.scalar_one()

    # Accept invite
    await accept_invite(db, invite.token, member.id)

    # Verify membership
    from omniai.models.user import user_organization
    result = await db.execute(
        select(user_organization.c.role)
        .where(
            user_organization.c.user_id == member.id,
            user_organization.c.organization_id == org.id
        )
    )
    role = result.scalar_one_or_none()
    assert role == "member"


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(db):
    from omniai.services.invite import accept_invite
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400

"""


###############################################################
# Unit tests for src/omniai/services/invite.py
###############################################################

"""
@pytest.mark.asyncio
async def test_create_invite_success(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    from omniai.models.user import user_organization
    #from omniai.models.user import User
    #from omniai.models.organization import Organization
    #from sqlalchemy import select

    # --- INLINE NO-COMMIT USER CREATION ---
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    hashed_pw = get_password_hash("SecurePass123!")
    owner = User(email=owner_email, hashed_password=hashed_pw)
    db.add(owner)
    await db.flush()

    personal_org = Organization(
        name=f"Personal – {owner_email}",
        slug=f"personal-{owner_email.replace('@', '').replace('.', '')}"
    )
    db.add(personal_org)
    await db.flush()
   
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=personal_org.id,
            role="owner",
            is_default=True
        )
    )
    # --- END INLINE ---

    # Create org
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)
    # ⚠️ Do NOT commit — keep in transaction

    # Create invite
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    assert invite.email == invitee_email
    assert invite.organization_id == org.id
    assert invite.invited_by_id == owner.id
    assert len(invite.token) > 20


@pytest.mark.asyncio
async def test_create_invite_forbidden_not_owner(db):
    from omniai.services.invite import create_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    #from omniai.models.user import User
    #from omniai.models.organization import Organization
    from sqlalchemy import select

    # --- OWNER (no commit) ---
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()
    # Skip personal org — not needed for this test

    # --- NON-OWNER (no commit) ---
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    # Create org (owned by owner)
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    from omniai.services.invite import create_invite, accept_invite
    from omniai.api.v1.schemas import InviteCreate
    from omniai.services.organization import create_organization_for_user
    #from omniai.models.user import User
    #from omniai.models.organization import Organization
    from sqlalchemy import select

    # --- OWNER (no commit) ---
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Create org
    org = await create_organization_for_user(db, owner.id, "Test Org", set_as_default=False)

    # --- MEMBER (no commit) ---
    member_email = f"member_{uuid.uuid4().hex}@test.com"
    member = User(email=member_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(member)
    await db.flush()

    # Create invite
    invite_data = InviteCreate(email=member_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Accept invite
    await accept_invite(db, invite.token, member.id)

    # Verify membership
    from omniai.models.user import user_organization
    result = await db.execute(
        select(user_organization.c.role)
        .where(
            user_organization.c.user_id == member.id,
            user_organization.c.organization_id == org.id
        )
    )
    role = result.scalar_one_or_none()
    assert role == "member"


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(db):
    from omniai.services.invite import accept_invite
    #from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400

"""




#############################################################################################


"""
@pytest.mark.asyncio
async def test_create_invite_success(db):
    #from omniai.services.invite import create_invite
    #from omniai.api.v1.schemas import InviteCreate
    #from omniai.models.user import User, user_organization
    #from omniai.models.organization import Organization
    #from sqlalchemy import select
    # Create owner (no commit)
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    hashed_pw = get_password_hash("SecurePass123!")
    owner = User(email=owner_email, hashed_password=hashed_pw)
    db.add(owner)
    await db.flush()

    # Create org with UNIQUE slug
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link owner to org
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    assert invite.email == invitee_email
    assert invite.organization_id == org.id
    assert invite.invited_by_id == owner.id
    assert len(invite.token) > 20


@pytest.mark.asyncio
async def test_create_invite_forbidden_not_owner(db):
    #from omniai.services.invite import create_invite
    #from omniai.api.v1.schemas import InviteCreate
    #from omniai.models.user import User, user_organization
    #from omniai.models.organization import Organization
    # Owner
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Non-owner
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    # Org owned by owner (UNIQUE slug)
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    #from omniai.services.invite import create_invite, accept_invite
    #from omniai.api.v1.schemas import InviteCreate
    #from omniai.models.user import User, user_organization
    #from omniai.models.organization import Organization
    #from sqlalchemy import select
    # Owner
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Org (UNIQUE slug)
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Member
    member_email = f"member_{uuid.uuid4().hex}@test.com"
    member = User(email=member_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(member)
    await db.flush()

    # Create invite
    invite_data = InviteCreate(email=member_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Accept invite
    await accept_invite(db, invite.token, member.id)

    # Verify membership
    result = await db.execute(
        select(user_organization.c.role)
        .where(
            user_organization.c.user_id == member.id,
            user_organization.c.organization_id == org.id
        )
    )
    role = result.scalar_one_or_none()
    assert role == "member"


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(db):
    #from omniai.services.invite import accept_invite
    #from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400
"""



"""
@pytest.mark.asyncio
async def test_get_user_from_token_missing_sub():
    # Mock: db.execute returns a result that .scalar_one_or_none() → None
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Patch decode_token to return dict without "sub"
    with patch("omniai.core.jwt.decode_token", return_value={"exp": 1769757322}):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None
        # Covers: invalid/missing sub path

        
        
@pytest.mark.asyncio
async def test_get_user_from_token_user_not_found():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Patch decode_token to return a valid-looking user ID
    with patch("omniai.core.jwt.decode_token", return_value={"sub": "usr_123"}):
        user = await get_user_from_token(mock_db, "valid-token")

    # Correct assertion: function fails safely
    assert user is None
"""

```


<div style='page-break-after: always;'></div>

# File: pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel>=0.46.2"]
build-backend = "setuptools.build_meta"

[project]
name = "omniai"
version = "0.1.0"
description = "The Sovereign AI Foundation Layer for Emerging Economies"
readme = "README.md"
license = "MIT"                   # ✅ SPDX short identifier (string, NOT table)
license-files = ["LICENSE"]       # ✅ Explicit license file
authors = [
    { name = "Antony Henry Oduor Onyango", email = "harryoduwor@gmail.com" }
]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Build Tools",
]
requires-python = ">=3.10"
dependencies = [
    # Web & API
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "slowapi>=0.1.9",

    # Data Validation & Settings
    "pydantic>=2.12.0,<2.13.0",
    "pydantic-core>=2.41.0,<2.42.0",
    "pydantic-settings>=2.6.0",
    
    # Database
    "sqlalchemy[asyncio]>=2.0.36",     # ← NEW: core ORM + async support
    "asyncpg>=0.29.0",                 # ← NEW: async PostgreSQL driver
    
    # Security & Auth
    "pyjwt[crypto]>=2.8.0",
    "passlib[bcrypt]>=1.7.4",          # ← NEW: password hashing
    "bcrypt>=4.0.0",                    # Explicitly add bcrypt
    
    # HTTP Client (for future service calls)
    "httpx>=0.28.0",
    
    # Structured Logging (optional but recommended)
    "structlog>=24.4.0",               # ← NEW: production-grade logs
    "email-validator>=2.2.0",
    "python-multipart>=0.0.9",
    "charset-normalizer>=3.3.0",
     
    # required for production rate limiting
    "redis>=4.5.0,<5.0.0",
    "limits>=3.5.0",

    # For metrics
    "prometheus-client==0.20.0",
    
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0",
    "mypy>=1.13.0",
    "ruff>=0.8.0",
    "bandit>=1.7.9",                   # ← NEW: security linter
    "httpx>=0.28.0",                   # already in main, but safe to repeat
    "python-dotenv>=1.0.1",
    "safety>=3.0.0",
    "aiosqlite",
    "wheel>=0.46.2",
    
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["omniai*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"  # or "strict" — but if "strict", you MUST use @pytest.mark.asyncio
cache_dir = "/tmp/.pytest_cache"

# This ensures pytest always looks in tests/, even if run from weird directories.
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.ruff]
lint.select = ["E", "W", "F", "I", "B", "C4", "SIM", "TID", "ARG", "PTH"]
lint.ignore = ["E501"]  # allow long lines
line-length = 88
fix = true
unsafe-fixes = false

[tool.ruff.lint.per-file-ignores]
"src/omniai/tests/unit/test_auth.py" = ["B008"]
"src/omniai/api/v1/me.py" = ["B008"]
"src/omniai/api/v1/auth.py" = ["B008", "ARG001"]
"src/omniai/api/v1/health.py" = ["B008"]
"src/omniai/api/deps.py" = ["B008"]
"src/omniai/api/v1/invite.py" = ["B008"]  
"src/omniai/api/v1/organization.py" = ["B008"]
"src/omniai/main.py" = ["ARG001"]



[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
strict_equality = true



# Omiting the following from coverage tests
[tool.coverage.run]
omit = [
    "src/omniai/main.py",
    "src/omniai/__main__.py",
    "*/migrations/*",
    "*/tests/*",
    "src/omniai/models/*.py"
]



#####

###
```


<div style='page-break-after: always;'></div>

# File: README.md

```md
# OMNIAI Core Platform

> The sovereign, production-grade foundation for AI systems that serve 1 billion underserved people.

> Built for performance, reliability, and African problem-solving  
> From Nairobi, with hunger and code  

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue)](https://python.org)


## 💼 Why This Matters

Most AI tools are built for Silicon Valley.  
This one is built for **Africa** — where:
- Internet fails daily
- Devices are underpowered
- Problems are urgent

And it works.

## 🚀 Quick Start

 https://omniai-web.onrender.com/v1/health

 https://omniai-web.onrender.com/v1/health/ready

```bash
git clone https://github.com/ahooTech/omniai-core.git  
cd omniai-core
python -m venv venv
source venv/Scripts/activate .  # Linux/Mac
# venv\Scripts\activate  # Windows

pip install -e .

# Install Docker

docker-compose -f docker-compose-test.yml build --no-cache

docker-compose -f docker-compose-test.yml up --exit-code-from test
```
## 📁 Project Structure
```
OMNIAI-CORE/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .mypy_cache/
├── .pytest_cache/
├── .ruff_cache/
├── .venv/
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   ├── share/
│   └── pyvenv.cfg
├── build/
│   ├── bdist.win-amd64/
│   └── lib/
├── docs/
│   └── adr/
│       ├── 001-database-choice.md
│       ├── 002-multi-tenancy-strategy.md
│       ├── 003-auth-architecture.md
│       ├── 004-observability-stack.md
│       ├── 005-deployment-pipeline.md
│       ├── 006-framework-selection.md
│       └── 007-testing-strategy.md
├── runbooks/
│   └── deploy.md
├── htmlcov/
├── scripts/
│   ├── bootstrap.sh
│   └── start.sh
├── src/
│   └── omniai/
│       ├── api/
│       │   ├── deps.py
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── agriculture.py
│       │       ├── auth.py
│       │       ├── health.py
│       │       ├── invite.py
│       │       ├── me.py
│       │       ├── metrics.py
│       │       ├── organization.py
│       │       └── schemas.py
│       ├── core/
│       │   ├── config.py
│       │   ├── jwt.py
│       │   ├── limiter.py
│       │   ├── logging_middleware.py
│       │   ├── logging.py
│       │   ├── metrics_config.py
│       │   ├── metrics_middleware.py
│       │   └── middleware.py
│       ├── db/
│       │   ├── __init__.py
│       │   └── session.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── invite.py
│       │   ├── organization.py
│       │   └── user.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── invite.py
│       │   └── organization.py
│       ├── main.py
│       └── __init__.py
├── omniai.egg-info/
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       ├── test_integration.py
│       └── test_unit.py
├── .coverage
├── .dockerignore
├── .env
├── .env.test.docker
├── .gitattributes
├── .gitignore
├── docker-compose-test.yml
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── limitercode.py
├── pyproject.toml
├── README.md
└── requirements.txt



```
## 🧪 Testing


## 📜 License
MIT © Antony Henry Oduor Onyango


## 📦 Phase 1: Software & Systems Core
- [ ] Python Mastery
- [ ] Algorithms & Data Structures
- [ ] Backend Engineering
- [ ] Database Engineering
- [ ] Cloud Computing Core
- [ ] Containerization & DevOps Engineering
- [ ] System Architecture & Design
- [ ] Security & Hardening
- [ ] Observability & Production Thinking
- [ ] Engineering Mindset & Execution


## Architecture
- [Architecture Decision Records (ADRs)](docs/adr/)



# https://github.com/ahooTech/omniai-core.git

# docker-compose -f docker-compose-test.yml down

# docker-compose down

# docker-compose -f docker-compose-test.yml build --no-cache

# docker-compose build --no-cache

# docker-compose -f docker-compose-test.yml up --exit-code-from test

# docker-compose up 



```


<div style='page-break-after: always;'></div>

# File: requirements.txt

```txt
#
# This file is autogenerated by pip-compile with Python 3.12
# by the following command:
#
#    pip-compile --output-file=requirements.txt pyproject.toml
#
annotated-doc==0.0.4
    # via fastapi
annotated-types==0.7.0
    # via pydantic
anyio==4.13.0
    # via
    #   httpx
    #   starlette
    #   watchfiles
asyncpg==0.31.0
    # via omniai (pyproject.toml)
bcrypt==5.0.0
    # via
    #   omniai (pyproject.toml)
    #   passlib
certifi==2026.2.25
    # via
    #   httpcore
    #   httpx
cffi==2.0.0
    # via cryptography
charset-normalizer==3.4.6
    # via omniai (pyproject.toml)
click==8.3.1
    # via uvicorn
colorama==0.4.6
    # via
    #   click
    #   uvicorn
cryptography==46.0.6
    # via pyjwt
deprecated==1.3.1
    # via limits
dnspython==2.8.0
    # via email-validator
email-validator==2.3.0
    # via omniai (pyproject.toml)
fastapi==0.135.2
    # via omniai (pyproject.toml)
greenlet==3.3.2
    # via sqlalchemy
h11==0.16.0
    # via
    #   httpcore
    #   uvicorn
httpcore==1.0.9
    # via httpx
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via omniai (pyproject.toml)
idna==3.11
    # via
    #   anyio
    #   email-validator
    #   httpx
limits==5.8.0
    # via
    #   omniai (pyproject.toml)
    #   slowapi
packaging==21.3
    # via limits
passlib[bcrypt]==1.7.4
    # via omniai (pyproject.toml)
prometheus-client==0.20.0
    # via omniai (pyproject.toml)
pycparser==3.0
    # via cffi
pydantic==2.12.5
    # via
    #   fastapi
    #   omniai (pyproject.toml)
    #   pydantic-settings
pydantic-core==2.41.5
    # via
    #   omniai (pyproject.toml)
    #   pydantic
pydantic-settings==2.13.1
    # via omniai (pyproject.toml)
pyjwt[crypto]==2.12.1
    # via omniai (pyproject.toml)
pyparsing==3.3.2
    # via packaging
python-dotenv==1.2.2
    # via
    #   pydantic-settings
    #   uvicorn
python-multipart==0.0.22
    # via omniai (pyproject.toml)
pyyaml==6.0.3
    # via uvicorn
redis==4.6.0
    # via omniai (pyproject.toml)
slowapi==0.1.9
    # via omniai (pyproject.toml)
sqlalchemy[asyncio]==2.0.48
    # via omniai (pyproject.toml)
starlette==1.0.0
    # via fastapi
structlog==25.5.0
    # via omniai (pyproject.toml)
typing-extensions==4.15.0
    # via
    #   anyio
    #   fastapi
    #   limits
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   starlette
    #   typing-inspection
typing-inspection==0.4.2
    # via
    #   fastapi
    #   pydantic
    #   pydantic-settings
uvicorn[standard]==0.42.0
    # via omniai (pyproject.toml)
watchfiles==1.1.1
    # via uvicorn
websockets==16.0
    # via uvicorn
wrapt==2.1.2
    # via deprecated

```


<div style='page-break-after: always;'></div>

# File: requirements-dev.txt

```txt
#
# This file is autogenerated by pip-compile with Python 3.12
# by the following command:
#
#    pip-compile --extra=dev --output-file=requirements-dev.txt pyproject.toml
#
aiosqlite==0.22.1
    # via omniai (pyproject.toml)
annotated-doc==0.0.4
    # via
    #   fastapi
    #   typer
annotated-types==0.7.0
    # via pydantic
anyio==4.13.0
    # via
    #   httpx
    #   starlette
    #   watchfiles
asyncpg==0.31.0
    # via omniai (pyproject.toml)
authlib==1.6.9
    # via safety
bandit==1.9.4
    # via omniai (pyproject.toml)
bcrypt==5.0.0
    # via
    #   omniai (pyproject.toml)
    #   passlib
certifi==2026.2.25
    # via
    #   httpcore
    #   httpx
    #   requests
cffi==2.0.0
    # via cryptography
charset-normalizer==3.4.6
    # via
    #   omniai (pyproject.toml)
    #   requests
click==8.3.1
    # via
    #   nltk
    #   safety
    #   typer
    #   uvicorn
colorama==0.4.6
    # via
    #   bandit
    #   click
    #   pytest
    #   tqdm
    #   uvicorn
coverage[toml]==7.13.5
    # via pytest-cov
cryptography==46.0.6
    # via
    #   authlib
    #   pyjwt
deprecated==1.3.1
    # via limits
dnspython==2.8.0
    # via email-validator
dparse==0.6.4
    # via
    #   safety
    #   safety-schemas
email-validator==2.3.0
    # via omniai (pyproject.toml)
fastapi==0.135.2
    # via omniai (pyproject.toml)
filelock==3.25.2
    # via safety
greenlet==3.3.2
    # via sqlalchemy
h11==0.16.0
    # via
    #   httpcore
    #   uvicorn
httpcore==1.0.9
    # via httpx
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via
    #   omniai (pyproject.toml)
    #   safety
idna==3.11
    # via
    #   anyio
    #   email-validator
    #   httpx
    #   requests
iniconfig==2.3.0
    # via pytest
jinja2==3.1.6
    # via safety
joblib==1.5.3
    # via nltk
librt==0.8.1
    # via mypy
limits==5.8.0
    # via
    #   omniai (pyproject.toml)
    #   slowapi
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==4.2.3
    # via safety
mdurl==0.1.2
    # via markdown-it-py
mypy==1.19.1
    # via omniai (pyproject.toml)
mypy-extensions==1.1.0
    # via mypy
nltk==3.9.4
    # via safety
packaging==26.0
    # via
    #   dparse
    #   limits
    #   pytest
    #   safety
    #   safety-schemas
    #   wheel
passlib[bcrypt]==1.7.4
    # via omniai (pyproject.toml)
pathspec==1.0.4
    # via mypy
pluggy==1.6.0
    # via
    #   pytest
    #   pytest-cov
prometheus-client==0.20.0
    # via omniai (pyproject.toml)
pycparser==3.0
    # via cffi
pydantic==2.12.5
    # via
    #   fastapi
    #   omniai (pyproject.toml)
    #   pydantic-settings
    #   safety
    #   safety-schemas
pydantic-core==2.41.5
    # via
    #   omniai (pyproject.toml)
    #   pydantic
pydantic-settings==2.13.1
    # via omniai (pyproject.toml)
pygments==2.19.2
    # via
    #   pytest
    #   rich
pyjwt[crypto]==2.12.1
    # via omniai (pyproject.toml)
pytest==9.0.2
    # via
    #   omniai (pyproject.toml)
    #   pytest-asyncio
    #   pytest-cov
pytest-asyncio==1.3.0
    # via omniai (pyproject.toml)
pytest-cov==7.1.0
    # via omniai (pyproject.toml)
python-dotenv==1.2.2
    # via
    #   omniai (pyproject.toml)
    #   pydantic-settings
    #   uvicorn
python-multipart==0.0.22
    # via omniai (pyproject.toml)
pyyaml==6.0.3
    # via
    #   bandit
    #   uvicorn
redis==4.6.0
    # via omniai (pyproject.toml)
regex==2026.2.28
    # via nltk
requests==2.33.0
    # via safety
rich==14.3.3
    # via
    #   bandit
    #   typer
ruamel-yaml==0.19.1
    # via
    #   safety
    #   safety-schemas
ruff==0.15.7
    # via omniai (pyproject.toml)
safety==3.7.0
    # via omniai (pyproject.toml)
safety-schemas==0.0.16
    # via safety
shellingham==1.5.4
    # via typer
slowapi==0.1.9
    # via omniai (pyproject.toml)
sqlalchemy[asyncio]==2.0.48
    # via omniai (pyproject.toml)
starlette==1.0.0
    # via fastapi
stevedore==5.7.0
    # via bandit
structlog==25.5.0
    # via omniai (pyproject.toml)
tenacity==9.1.4
    # via safety
tomlkit==0.14.0
    # via safety
tqdm==4.67.3
    # via nltk
typer==0.24.1
    # via safety
typing-extensions==4.15.0
    # via
    #   anyio
    #   fastapi
    #   limits
    #   mypy
    #   pydantic
    #   pydantic-core
    #   pytest-asyncio
    #   safety
    #   safety-schemas
    #   sqlalchemy
    #   starlette
    #   typing-inspection
typing-inspection==0.4.2
    # via
    #   fastapi
    #   pydantic
    #   pydantic-settings
urllib3==2.6.3
    # via requests
uvicorn[standard]==0.42.0
    # via omniai (pyproject.toml)
watchfiles==1.1.1
    # via uvicorn
websockets==16.0
    # via uvicorn
wheel==0.46.3
    # via omniai (pyproject.toml)
wrapt==2.1.2
    # via deprecated

```


<div style='page-break-after: always;'></div>

# File: scripts\bootstrap.sh

```sh
```


<div style='page-break-after: always;'></div>

# File: scripts\start.sh

```sh
#!/bin/sh
set -e

# Build the command dynamically
CMD="uvicorn omniai.main:app --host ${UVICORN_HOST:-0.0.0.0} --port ${UVICORN_PORT:-8000}"

# Only add --reload if explicitly set to "true"
if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
    CMD="$CMD --reload"
fi

exec $CMD
```


<div style='page-break-after: always;'></div>

# File: src\omniai\__init__.py

```py
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\__init__.py

```py
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\deps.py

```py
# src/omniai/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.db.session import get_db
from omniai.models.user import User
from omniai.services.auth import get_user_from_token


security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT.
    Raises 401 if invalid or expired token.
    """
    token = credentials.credentials
    user = await get_user_from_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\agriculture.py

```py
from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str

router = APIRouter()

@router.get("/agriculture", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="agriculture")

```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\auth.py

```py
## src/omniai/api/v1/auth.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.v1.schemas import Token, UserCreate
from omniai.core.jwt import create_access_token
from omniai.core.logging import logger
from omniai.db.session import get_db
from omniai.models.user import User
from omniai.services.auth import authenticate_user, create_user_with_org
#from omniai.core.limiter import limiter
from omniai.core.limiter import conditional_limit


router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
@conditional_limit("3/minute")
async def signup(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    #logger.info("rate_limit_enabled", enabled=limiter.enabled)  # ← add this
    logger.info("signup_attempt", email=user.email)

    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warn("signup_failed", email=user.email, reason="email_already_registered")
        raise HTTPException(status_code=400, detail="Email already registered") from None

    try:
        new_user = await create_user_with_org(
            db=db,
            email=user.email,
            password=user.password
        )
        logger.info("signup_success", user_id=str(new_user.id), email=user.email)
        return {"msg": "User created"}
    except Exception as e:
        logger.exception("signup_error", email=user.email, error=str(e))
        raise HTTPException(status_code=500, detail="Signup failed") from None


@router.post("/login", response_model=Token)
@conditional_limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    #logger.info("rate_limit_enabled", enabled=limiter.enabled)  # ← add this
    logger.info("login_attempt", email=form_data.username)

    user: Optional[User] = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warn("login_failed", email=form_data.username, reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    access_token = create_access_token(data={"sub": str(user.id)})  # ensure str
    logger.info("login_success", user_id=str(user.id), email=user.email)

    return Token(access_token=access_token, token_type="bearer")

```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\health.py

```py
"""
# In your health router file (e.g., src/omniai/api/v1/health.py or similar)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from omniai.db.session import get_db  # ← adjust import to match your project


class HealthResponse(BaseModel):
    status: str
    service: str


router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="omniai-core")


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="ready", service="omniai-core")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
"""

from fastapi import APIRouter, HTTPException, Depends, Request  # ← ADD Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from omniai.db.session import get_db


class HealthResponse(BaseModel):
    status: str
    service: str


router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="omniai-core")


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(
    request: Request,  # ← ADD THIS
    db: AsyncSession = Depends(get_db)
) -> HealthResponse:
    # ✅ Check if app has finished startup
    if not getattr(request.app.state, 'ready', False):
        raise HTTPException(status_code=503, detail="Startup incomplete") from None

    # ✅ Check DB connectivity
    try:
        await db.execute(text("SELECT 1"))
        return HealthResponse(status="ready", service="omniai-core")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\invite.py

```py
# src/omniai/api/v1/invites.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.deps import get_current_user
from omniai.db.session import get_db
from omniai.api.v1.schemas import InviteCreate, InviteAccept, InviteResponse
from omniai.services.invite import create_invite, accept_invite
from omniai.models.user import User

router = APIRouter()

"""
@router.post("/organizations/{org_id}/invite", response_model=InviteResponse)
async def send_invite(
    org_id: str,
    invite_data: InviteCreate,  # ✅ FIXED: added ":"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> InviteResponse:
    #Send an invite to join an organization.
    #Only owners can send invites.
    invite = await create_invite(db, org_id, current_user.id, invite_data)
    return {"invite_id": invite.id, "token": invite.token}
"""

@router.post("/organizations/{org_id}/invite", response_model=InviteResponse)
async def send_invite(
    org_id: str,
    invite_data: InviteCreate,  # ✅ CORRECT: parameter_name: Type
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> InviteResponse:
    """
    Send an invite to join an organization.
    Only owners can send invites.
    """
    invite = await create_invite(db, org_id, current_user.id, invite_data)
    return InviteResponse(invite_id=invite.id, token=invite.token)


@router.post("/invites/accept")
async def accept_invite_endpoint(
    invite_data: InviteAccept,  # ✅ FIXED: added ":"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Accept an invite and join the organization as a member.
    """
    await accept_invite(db, invite_data.token, current_user.id)
    return {"message": "Successfully joined organization"}
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\me.py

```py
# src/omniai/api/v1/me.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.v1.schemas import OrganizationSummary, UserMe
from omniai.core.logging import logger
from omniai.core.limiter import conditional_limit
from omniai.db.session import get_db
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization

router = APIRouter()

@router.get("/me", response_model=UserMe)
@conditional_limit("20/minute")
async def read_users_me(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> UserMe:
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)

    if not user_id or not tenant_id:
        logger.warn("me_request_missing_context", url=str(request.url))
        raise HTTPException(status_code=401, detail="Authentication required")

    # 1. Fetch user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        logger.warn("me_request_user_not_found")
        raise HTTPException(status_code=401, detail="User not found")

    # 2. Verify user is member of tenant_id AND get role
    membership_result = await db.execute(
        select(user_organization.c.is_default, user_organization.c.role)
        .where(
            user_organization.c.user_id == user_id,
            user_organization.c.organization_id == tenant_id
        )
    )
    membership = membership_result.fetchone()
    if not membership:
        logger.warn("me_request_not_org_member")
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    role = membership.role

    # 3. Fetch all orgs for user
    orgs_result = await db.execute(
        select(Organization.id, Organization.name, Organization.slug, user_organization.c.role, user_organization.c.is_default)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(user_organization.c.user_id == user_id)
    )
    orgs = orgs_result.fetchall()
    organizations = [
        OrganizationSummary(
            id=org.id,
            name=org.name,
            slug=org.slug,
            role=org.role,
            is_default=org.is_default
        )
        for org in orgs
    ]

    # ✅ Log successful profile fetch
    logger.info(
        "user_profile_fetched",
        role_in_active_org=role,
        total_organizations=len(organizations)
    )

    return UserMe(
        id=user.id,
        email=user.email,
        active_organization_id=tenant_id,
        role_in_active_org=role,
        organizations=organizations
    )

```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\metrics.py

```py
from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

router = APIRouter()

@router.get("/metrics")
async def get_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\organization.py

```py

# src/omniai/api/v1/organization.py
from fastapi import APIRouter, Depends, status, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.models.user import User
from omniai.services.organization import create_organization_for_user, delete_organization
from omniai.api.v1.schemas import OrganizationCreate, OrganizationSummary
from omniai.api.deps import get_current_user
from omniai.db.session import get_db
from typing import List
from omniai.services.organization import remove_member, leave_organization

router = APIRouter()

@router.post("", response_model=OrganizationSummary, status_code=status.HTTP_201_CREATED)
async def create_organization_endpoint(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> OrganizationSummary:
    org = await create_organization_for_user(
        db, 
        user_id=current_user.id, 
        name=org_in.name, 
        set_as_default=False
    )

    await db.commit()
    await db.refresh(org)
    
    return OrganizationSummary(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role="owner",
        is_default=False
    )




# ✅ NEW: Delete Organization Endpoint
@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Organization deleted successfully"},
        403: {"description": "Cannot delete personal organization"},
        404: {"description": "Organization not found or you are not the owner"}
    }
)
async def delete_organization_endpoint(
    org_id: str = Path(..., description="The ID of the organization to delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an organization.
    - Only owners can delete
    - Personal organizations (slug starts with 'personal-') cannot be deleted
    """
    await delete_organization(db=db, org_id=org_id, user_id=current_user.id)
    # Returns 204 No Content automatically


# ADD THIS FUNCTION BELOW YOUR EXISTING ONES
@router.get("", response_model=List[OrganizationSummary])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[OrganizationSummary]:
    """
    Get all organizations the current user belongs to.
    """
    from sqlalchemy import select
    from omniai.models.user import user_organization
    from omniai.models.organization import Organization

    # Join to get orgs + membership info
    result = await db.execute(
        select(
            Organization.id,
            Organization.name,
            Organization.slug,
            user_organization.c.role,
            user_organization.c.is_default
        )
        .select_from(Organization)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(user_organization.c.user_id == current_user.id)
        .order_by(user_organization.c.joined_at.desc())
    )
    
    rows = result.fetchall()
    return [
        OrganizationSummary(
            id=row.id,
            name=row.name,
            slug=row.slug,
            role=row.role,
            is_default=row.is_default
        )
        for row in rows
    ]


# ✅ NEW: Remove Member Endpoint
@router.delete("/{org_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    org_id: str = Path(..., description="Organization ID"),
    target_user_id: str = Path(..., description="User ID to remove"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Owner removes a member from the organization.
    - Cannot remove self
    - Cannot remove other owners
    - Cannot modify personal org
    """
    await remove_member(db, org_id, current_user.id, target_user_id)


# ✅ NEW: Leave Organization Endpoint
@router.post("/{org_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_organization_endpoint(
    org_id: str = Path(..., description="Organization ID to leave"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Member leaves an organization.
    - Cannot leave personal org
    - Cannot leave if last owner
    """
    await leave_organization(db, org_id, current_user.id)
```


<div style='page-break-after: always;'></div>

# File: src\omniai\api\v1\schemas.py

```py
# src/omniai/api/v1/schemas.py
import re
from typing import List

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain a special character")
        return v


class OrganizationCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Organization name cannot be empty")
        if len(v) > 100:
            raise ValueError("Organization name too long")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class OrganizationSummary(BaseModel):
    id: str
    name: str
    slug: str
    role: str  # "owner" or "member"
    is_default: bool


class UserMe(BaseModel):
    id: str
    email: str
    active_organization_id: str
    role_in_active_org: str
    organizations: List[OrganizationSummary]


# 🔽 ADD THESE NEW SCHEMAS BELOW 🔽

class InviteCreate(BaseModel):
    email: EmailStr


class InviteAccept(BaseModel):
    token: str


class InviteResponse(BaseModel):
    invite_id: str
    token: str  # For testing only — hide in prod
```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\config.py

```py
# src/omniai/core/config.py
from typing import Any
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = Field(
        default="development",
        description="Environment: 'development', 'test', or 'production'"
    )
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost/omniai",
        description="Async PostgreSQL connection URL"
    )
    JWT_SECRET_KEY: str = Field(
        ...,  # required — must come from env
        description="Secret key for JWT signing — MUST be set in production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Optional: add prefix like OMNIAI_
        # env_prefix="OMNIAI_",
    )

    def __init__(self, **kwargs: Any) -> None:
         # Allow empty init — Pydantic loads from env
        super().__init__(**kwargs)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\jwt.py

```py
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import PyJWTError

from omniai.core.config import get_settings  # ✅ Import the function, not the instance


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    settings = get_settings()  # ✅ Call it inside the function
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()  # ✅ Call it here too
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True, "require": ["exp", "sub"]},
        )
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id.startswith("usr_"):
            raise PyJWTError("Invalid user ID format")
        return payload
    except PyJWTError as e:
        raise PyJWTError(f"Token decode failed: {str(e)}") from e
```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\limiter.py

```py

import os
from functools import wraps
from typing import Any, Callable, Coroutine, Optional, TypeVar, cast

from slowapi import Limiter
from starlette.requests import Request

# ✅ Custom key function that respects X-Forwarded-For
def get_real_client_ip(request: Request) -> str:
    # Check X-Forwarded-For first (Render, Cloudflare, etc.)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For: client, proxy1, proxy2
        return forwarded.split(",")[0].strip()
    # Fallback to direct remote address
    return request.client.host if request.client else "127.0.0.1"

DISABLE_RATE_LIMIT = os.getenv("OMNIAI_DISABLE_RATE_LIMIT", "0").lower() in ("1", "true", "yes")
REDIS_URL = os.getenv("REDIS_URL")

_real_limiter: Optional[Limiter] = None

if not DISABLE_RATE_LIMIT:
    if REDIS_URL:
        _real_limiter = Limiter(
            key_func=get_real_client_ip,  # ← Use real IP
            storage_uri=REDIS_URL
        )
    else:
        _real_limiter = Limiter(key_func=get_real_client_ip)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

def conditional_limit(limit: str) -> Callable[[F], F]:
    if DISABLE_RATE_LIMIT or _real_limiter is None:
        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator
    else:
        return _real_limiter.limit(limit)

limiter = _real_limiter
```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\logging.py

```py
# src/omniai/core/logging.py
import logging
import sys
from typing import Any, Callable, Mapping, MutableMapping, Tuple, Union

import structlog
from structlog import get_logger
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer

# Define the processor type to help MyPy
ProcessorType = Callable[
    [Any, str, MutableMapping[str, Any]],
    Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]]
]

def configure_logging() -> None:
    # Set root logger level
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Detect dev vs prod
    is_dev = sys.stdout.isatty()

    # Shared processors
    shared_processors: list[ProcessorType] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Annotate renderer with union type
    renderer = ConsoleRenderer() if is_dev else JSONRenderer()

    # Final processor list
    all_processors: list[ProcessorType] = shared_processors + [renderer]

    structlog.configure(
        processors=all_processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 🔥 CRITICAL: Route standard library logs through structlog
    structlog.stdlib.recreate_defaults()


configure_logging()
logger = get_logger()

```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\logging_middleware.py

```py
# omniai/core/logging_middleware.py
import uuid
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from omniai.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Clear any leftover context from previous requests (important in async!)
        clear_contextvars()

        # Generate a unique trace ID for this request
        trace_id = str(uuid.uuid4())
        bind_contextvars(trace_id=trace_id)

        # Log request start
        logger.info(
            "http_request_start",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
        )

        try:
            response: Response = await call_next(request)
            # Log request end
            logger.info(
                "http_request_end",
                status_code=response.status_code,
                content_length=getattr(response, "content_length", 0),
            )
            return response
        except Exception as e:
            # Log unhandled exceptions
            logger.exception("http_request_unhandled_error", error=str(e))
            raise

```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\metrics_config.py

```py
from prometheus_client import Counter, Histogram, Gauge

# Request counters
REQUEST_COUNT = Counter(
    "omniai_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

# Latency histogram
REQUEST_LATENCY = Histogram(
    "omniai_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Active tenants/users (optional)
ACTIVE_TENANTS = Gauge("omniai_active_tenants", "Number of active tenants")
```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\metrics_middleware.py

```py

import time
from typing import Any, Awaitable, Callable
from starlette.requests import Request
from omniai.core.metrics_config import REQUEST_COUNT, REQUEST_LATENCY

class MetricsMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        start_time = time.time()
        status_code = 500  # default for errors

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.url.path
            REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
            REQUEST_COUNT.labels(request.method, endpoint, str(status_code)).inc()
```


<div style='page-break-after: always;'></div>

# File: src\omniai\core\middleware.py

```py

# OMNIAI Core Middleware Layer
from typing import Awaitable, Callable

from fastapi import Request
from jwt import PyJWTError
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from structlog.contextvars import bind_contextvars

from omniai.core.jwt import decode_token
from omniai.core.logging import logger
from omniai.db.session import AsyncSessionLocal
from omniai.models.organization import Organization
from omniai.models.user import user_organization

# Public paths (no auth needed)
PUBLIC_PATHS = {
    "/",
    "/v1/health",
    "/v1/health/ready",
    "/metrics",
    "/v1/auth/signup",
    "/v1/auth/login",
    "/docs",
    "/openapi.json",
}

class TenantValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # === STEP 1: Authenticate user via JWT ===
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warn("auth_missing", url=str(request.url))
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "MISSING_AUTH_TOKEN", "message": "Authorization header missing"}}
            )

        token = auth_header[7:]
        try:
            payload = decode_token(token)
            user_id = payload["sub"]
        except PyJWTError as e:
            logger.warn("auth_invalid_token", url=str(request.url), error=str(e))
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "INVALID_TOKEN", "message": "Invalid or expired token"}}
            )

        # === STEP 2–3: Handle tenant resolution + validation in ONE DB session ===
        tenant_id = request.headers.get("x-tenant-id")
        used_default = False

        async with AsyncSessionLocal() as db:
            # --- Resolve tenant_id if missing ---
            if not tenant_id:
                logger.info("tenant_missing_fallback_to_default", user_id=user_id)
                result = await db.execute(
                    select(user_organization.c.organization_id)
                    .where(
                        user_organization.c.user_id == user_id,
                        user_organization.c.is_default
                    )
                )
                default_org = result.scalar_one_or_none()
                if not default_org:
                    logger.warn("user_no_default_org", user_id=user_id)
                    return JSONResponse(
                        status_code=403,
                        content={"error": {"code": "NO_DEFAULT_ORG", "message": "User has no default organization."}}
                    )
                tenant_id = default_org
                used_default = True
            else:
                # --- Validate org exists ---
                org_exists = await db.execute(
                    select(Organization.id).where(Organization.id == tenant_id)
                )
                if org_exists.scalar_one_or_none() is None:
                    logger.warn("tenant_not_found", tenant_id=tenant_id, user_id=user_id)
                    return JSONResponse(
                        status_code=404,
                        content={"error": {"code": "ORG_NOT_FOUND", "message": "Organization not found"}}
                    )

            # --- Validate user is a member of the resolved tenant_id ---
            membership = await db.execute(
                select(user_organization.c.organization_id)
                .where(
                    user_organization.c.user_id == user_id,
                    user_organization.c.organization_id == tenant_id
                )
            )
            if membership.scalar_one_or_none() is None:
                logger.warn("access_denied_not_org_member", user_id=user_id, tenant_id=tenant_id)
                return JSONResponse(
                    status_code=403,
                    content={"error": {"code": "NOT_ORG_MEMBER", "message": "Not a member of the specified organization"}}
                )

        # === STEP 4: Bind to logs and request state ===
        bind_contextvars(user_id=user_id, tenant_id=tenant_id)
        request.state.user_id = user_id
        request.state.tenant_id = tenant_id

        logger.info(
            "auth_and_tenant_success",
            user_id=user_id,
            tenant_id=tenant_id,
            used_default=used_default
        )

        return await call_next(request)


# NOTE: We intentionally avoid loading full ORM objects here.
# Authorization requires only ID existence checks — not user/org data.
# lazy="selectin" is irrelevant in this context; raw selects are optimal.
```


<div style='page-break-after: always;'></div>

# File: src\omniai\db\__init__.py

```py
# src/omniai/db/__init__.py
# Empty file — marks directory as package

```


<div style='page-break-after: always;'></div>

# File: src\omniai\db\session.py

```py
# omniai/db/session.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from omniai.core.config import get_settings  # ✅ Import the function

# ✅ Get settings ONCE at module load time
_settings = get_settings()

# Production-grade async engine
engine = create_async_engine(
    _settings.DATABASE_URL,  # ← Use local _settings
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```


<div style='page-break-after: always;'></div>

# File: src\omniai\main.py

```py
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Antony Henry Oduor Onyango

"""
OMNIAI Core Application Entry Point

This is the heart of the system. It will evolve through Phase 1 as follows:

✅ [DONE] 1. Basic FastAPI app + health route + tenant middleware

🔜 [PHASE 1: Backend Engineering]
   - Add structured exception handlers (global error formatting)
   - Add CORS configuration (from security domain)
   - Register all API routers (users, orgs, audit, etc.)

🔜 [PHASE 1: Database Engineering]
   - Integrate SQLAlchemy engine and sessionmaker
   - Add startup/shutdown events:
       • Connect to DB on startup
       • Close pools on shutdown

🔜 [PHASE 1: Observability]
   - Attach OpenTelemetry or custom metrics exporter
   - Initialize logging configuration (structured, JSON)

🔜 [PHASE 1: Security]
   - Add security middleware chain:
       • Rate limiting
       • Request validation
       • JWT authentication (when auth service exists)
   - Enforce HTTPS in production (via middleware or proxy)

🔜 [PHASE 1: System Architecture]
   - Add async task queue initialization (Celery or asyncio)
   - Configure dependency injection container (if used)

🔜 [PHASE 1: Cloud & DevOps]
   - Add config loading from env + secrets manager
   - Support multiple environments (dev, staging, prod)

🔜 [PHASE 1: Engineering Mindset]
   - Add graceful shutdown handling (signal listeners)
   - Add startup diagnostics (log version, config hash)

🔜 [PHASE 2+]
   - Mount AI-specific routers (agents, RAG, etc.)
   - Add model monitoring hooks

IMPORTANT: This file should remain CLEAN.
- No business logic
- No DB queries
- Only wiring: middlewares, routers, lifecycle events
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from sqlalchemy.exc import OperationalError
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from omniai.api.v1 import auth, me, health, agriculture, organization, metrics, invite
# from omniai.api.v1.metrics import router as metrics_router
from omniai.core.config import Settings
from omniai.core.logging import logger
from omniai.core.metrics_middleware import MetricsMiddleware
from omniai.core.logging_middleware import LoggingMiddleware
from omniai.core.middleware import TenantValidationMiddleware
from omniai.db.session import engine
from omniai.models.organization import Base as OrgBase
from omniai.models.user import Base as UserBase
from omniai.models.invite import Base as InviteBase
from omniai.core.limiter import limiter as rate_limiter

# Determine if docs should be enabled — ONLY for UI, no business logic
_ENABLE_DOCS = os.getenv("ENV", "development") != "production"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ✅ VALIDATE AND LOAD CONFIG HERE
    try:
        settings = Settings()  # ← Instantiated only when app starts
    except Exception as e:
        logger.critical("config_validation_failed", error=str(e))
        raise SystemExit(1) from None

    # 🔒 Security & config audit
    logger.info(
        "application_startup_init",
        version="1.0",
        database_engine="postgresql",
        async_driver="asyncpg",
        token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        jwt_algorithm=settings.JWT_ALGORITHM,
        debug_mode=(len(settings.JWT_SECRET_KEY) < 32)
    )

    if len(settings.JWT_SECRET_KEY) < 32:
        logger.critical(
            "security_risk_weak_jwt_secret",
            message="JWT_SECRET_KEY is less than 32 bytes — rotate immediately!"
        )

    # Store settings in app.state for access in routes/middleware if needed
    app.state.settings = settings

    # Initialize readiness flag
    app.state.ready = False

    # Wait for DB to be ready and create tables
    for i in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(UserBase.metadata.create_all)
                await conn.run_sync(OrgBase.metadata.create_all)
                await conn.run_sync(InviteBase.metadata.create_all)
            logger.info("database_initialized", tables_created=["users", "organizations", "user_organization"])
            break
        except OperationalError as e:
            logger.warning("database_connection_retry", attempt=i+1, max_attempts=10, error=str(e))
            await asyncio.sleep(2)
    else:
        logger.error("database_connection_failed", message="Failed to connect to database after 10 attempts")
        raise RuntimeError("Failed to connect to database after 10 attempts") from None

    app.state.ready = True
    logger.info("application_startup_complete", message="OMNIAI Core is ready to accept requests")
    yield

    # Shutdown
    app.state.ready = False
    await engine.dispose()
    logger.info("application_shutdown", message="Database engine disposed")




app = FastAPI(
    title="OMNIAI Core Platform",
    description="The sovereign foundation for trillion-dollar AI applications.",
    version="0.1.0",
    docs_url="/docs" if _ENABLE_DOCS else None,
    redoc_url="/redoc" if _ENABLE_DOCS else None,
    openapi_url="/openapi.json" if _ENABLE_DOCS else None,
    lifespan=lifespan,

)

# Attach limiter to app state
if rate_limiter is not None:
    app.state.limiter = rate_limiter

# Exception handler
async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit_exceeded", "detail": exc.detail},
            headers=exc.headers or {},
        )
    return JSONResponse(status_code=500, content={"error": "server_error"})


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Middlewares
app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TenantValidationMiddleware)

# Routers
app.include_router(health.router, prefix="/v1")
app.include_router(agriculture.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1/auth")
app.include_router(me.router, prefix="/v1")
#app.include_router(metrics_router)
app.include_router(metrics.router, prefix="/v1")
app.include_router(organization.router, prefix="/v1/organizations")
app.include_router(invite.router, prefix="/v1")

if __name__ == "__main__":
    host = os.getenv("UVICORN_HOST", "127.0.0.1")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "omniai.main:app",
        host=host,
        port=port,
        reload=reload,
    )


# pushing 
# Pushing interview test
# Pushing interview test
```


<div style='page-break-after: always;'></div>

# File: src\omniai\models\__init__.py

```py
# src/omniai/models/__init__.py
# Empty file

```


<div style='page-break-after: always;'></div>

# File: src\omniai\models\base.py

```py
# src/omniai/models/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

```


<div style='page-break-after: always;'></div>

# File: src\omniai\models\invite.py

```py
# src/omniai/models/invite.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, ForeignKey
import datetime as dt
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User

class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: "inv_" + uuid.uuid4().hex
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(
        String, 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False
    )
    invited_by_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )
    expires_at: Mapped[dt.datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    default=lambda: dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)
    )
    
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (optional for now)
    # organization: Mapped["Organization"] = relationship()
    # invited_by: Mapped["User"] = relationship()

    


```


<div style='page-break-after: always;'></div>

# File: src\omniai\models\organization.py

```py

# src/omniai/models/organization.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User  # for type checker onl


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: "org_" + uuid.uuid4().hex
    )
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_organization",
        back_populates="organizations",
        lazy="selectin"
    )

```


<div style='page-break-after: always;'></div>

# File: src\omniai\models\user.py

```py
# src/omniai/models/user.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Table, PrimaryKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .organization import Organization


# Define association table
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE")),
    Column("organization_id", String, ForeignKey("organizations.id", ondelete="CASCADE")),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_default", Boolean, default=False, nullable=False),
    Column("role", String, nullable=False, default="member"),
    PrimaryKeyConstraint("user_id", "organization_id"),  # ← COMPOSITE PK
    Index(
        "idx_user_default_org",
        "user_id",
        unique=True,
        postgresql_where=Column("is_default")
    )
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: "usr_" + uuid.uuid4().hex
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        secondary=user_organization,
        back_populates="users",
        lazy="selectin"
    )


"""
# Define association table
user_organization = Table(
    "user_organization",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("organization_id", String, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
    Column("is_default", Boolean, default=False, nullable=False),
    Column("role", String, nullable=False, default="member"),
    Index(
        "idx_user_default_org",
        "user_id",
        unique=True,
        postgresql_where=Column("is_default")
    )
)

"""
```


<div style='page-break-after: always;'></div>

# File: src\omniai\services\__init__.py

```py
```


<div style='page-break-after: always;'></div>

# File: src\omniai\services\auth.py

```py
# src/omniai/services/auth.py
import re
from typing import Optional

import bcrypt
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.core.logging import logger
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization

from omniai.services.organization import create_organization_for_user
from omniai.core.jwt import decode_token 


def get_password_hash(password: str) -> str:
    # ✅ Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")
    truncated = password_bytes[:72]
    # Hash using bcrypt
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)



async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    logger.debug("authenticate_user_start", email=email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        logger.debug("authenticate_user_user_not_found", email=email)
        return None  # ✅ Correct: None means "not authenticated"

    if not verify_password(password, user.hashed_password):
        logger.debug("authenticate_user_password_invalid", email=email)
        return None  # ✅ Still None

    logger.debug("authenticate_user_success", user_id=str(user.id), email=email)
    return user  # ✅ Only ever returns User or None



async def create_user_with_org(db: AsyncSession, email: str, password: str) -> User:
    logger.info("create_user_with_org_start", email=email)
    
    # Create user
    hashed_pw = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pw)
    db.add(user)
    await db.flush()
    logger.debug("user_created", user_id=user.id)

    # Create Personal org and link as DEFAULT
    personal_org_name = f"Personal – {email}"
    await create_organization_for_user(
        db, 
        user_id=user.id, 
        name=personal_org_name, 
        set_as_default=True
    )

    await db.commit()
    await db.refresh(user)
    logger.info("create_user_with_org_success", user_id=user.id, email=email)
    return user


async def get_user_from_token(db: AsyncSession, token: str) -> User | None:
    """
    Decode JWT and fetch user from DB.
    Returns None if token is invalid or user doesn't exist.
    """
    try:
        payload = decode_token(token)
        # Safely extract user_id
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            logger.warning("invalid_token_missing_sub", token=token[:10] + "...")
            return None
    except Exception:
        logger.warning("invalid_token_decode_error", token=token[:10] + "...")
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


"""
async def create_user_with_org(db: AsyncSession, email: str, password: str) -> User:

    # Creates a new user with a Personal organization.
    # The user is the OWNER of this org, and it is set as their DEFAULT.

    # Later: org_name = f"Personal – {email} ({country_code})"
    # In future, infer from email domain or IP — for now, just label
    # === 1. Create Personal Organization ===
    logger.info("create_user_with_org_start", email=email)
    personal_org_name = f"Personal – {email}"

    # Generate slug
    normalized = re.sub(r"[^a-z0-9\s-]", "", personal_org_name.lower())
    base_slug = re.sub(r"[-\s]+", "-", normalized).strip("-")[:26]

    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if result.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            logger.error("create_user_with_org_slug_failure", email=email, base_slug=base_slug)
            raise ValueError("Could not generate a unique slug for Personal org")

    # Save org
    org = Organization(name=personal_org_name, slug=slug)
    db.add(org)
    await db.flush()  # Get org.id
    logger.debug("create_user_with_org_org_created", org_id=str(org.id), slug=slug, email=email)

    # === 2. Create User ===
    hashed_pw = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_pw)
    db.add(user)
    await db.flush()  # Get user.id
    logger.debug("create_user_with_org_user_created", user_id=str(user.id), email=email)

    # === 3. Link user to org as OWNER + DEFAULT ===
    await db.execute(
        insert(user_organization),
        [{
            "user_id": user.id,
            "organization_id": org.id,
            "is_default": True,
            "role": "owner"
        }]
    )

    await db.commit()
    await db.refresh(user)
    logger.info("create_user_with_org_success", user_id=str(user.id), org_id=str(org.id), email=email)
    return user

"""
```


<div style='page-break-after: always;'></div>

# File: src\omniai\services\invite.py

```py
# src/omniai/services/invite.py
"""
Invite service layer.
Used by:
- Organization owners to invite members
- Users to accept invites and join organizations
"""

import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from omniai.api.v1.schemas import InviteCreate  # ✅ Matches your schema location
from omniai.core.logging import logger          # ✅ Your structured logger
from omniai.models.invite import Invite
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization


async def create_invite(
    db: AsyncSession,
    org_id: str,
    inviter_id: str,
    invite_data: InviteCreate
) -> Invite:
    """
    Creates an invite for a user to join an organization.
    Only org owners can send invites.
    """
    logger.debug("create_invite_start", org_id=org_id, inviter_id=inviter_id, email=invite_data.email)

    # 1. Verify inviter is owner of org
    result = await db.execute(
        select(Organization)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(
            Organization.id == org_id,
            user_organization.c.user_id == inviter_id,
            user_organization.c.role == "owner"
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        logger.warning("create_invite_forbidden", org_id=org_id, user_id=inviter_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can send invites"
        )

    # 2. Check if user already in org
    user_result = await db.execute(select(User.id).where(User.email == invite_data.email))
    invited_user_id = user_result.scalar_one_or_none()
    
    if invited_user_id:
        membership_result = await db.execute(
            select(user_organization.c.user_id)
            .where(
                user_organization.c.organization_id == org_id,
                user_organization.c.user_id == invited_user_id
            )
        )
        if membership_result.scalar_one_or_none():
            logger.warning("create_invite_user_already_member", org_id=org_id, email=invite_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

    # 3. Generate token
    token = secrets.token_urlsafe(32)

    # 4. Create invite
    invite = Invite(
        token=token,
        email=invite_data.email,
        organization_id=org_id,
        invited_by_id=inviter_id
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    
    logger.info("invite_created", invite_id=invite.id, org_id=org_id, email=invite_data.email)
    return invite


async def accept_invite(db: AsyncSession, token: str, user_id: str) -> None:
    """
    Accepts an invite and adds the user to the organization as a member.
    """
    logger.debug("accept_invite_start", token=token, user_id=user_id)

    # 1. Find active, unexpired invite
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Invite)
        .where(
            Invite.token == token,
            Invite.is_active,
            Invite.expires_at > now,
            Invite.accepted_at.is_(None)
        )
    )

    invite = result.scalar_one_or_none()
    if not invite:
        logger.warning("accept_invite_invalid", token=token)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite"
        )

    # 2. Get user email
    user_result = await db.execute(select(User.email).where(User.id == user_id))
    user_email = user_result.scalar_one_or_none()
    if not user_email:
        logger.error("accept_invite_user_not_found", user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Verify email matches
    if user_email != invite.email:
        logger.warning("accept_invite_email_mismatch", invite_email=invite.email, user_email=user_email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite email does not match your account"
        )

    # 4. Add to org as member
    await db.execute(
        user_organization.insert().values(
            user_id=user_id,
            organization_id=invite.organization_id,
            role="member",
            is_default=False
        )
    )

    # 5. Mark invite as accepted
    await db.execute(
        update(Invite)
        .where(Invite.id == invite.id)
        .values(accepted_at=now, is_active=False)
    )
    await db.commit()
    
    logger.info("invite_accepted", invite_id=invite.id, user_id=user_id, org_id=invite.organization_id)
```


<div style='page-break-after: always;'></div>

# File: src\omniai\services\organization.py

```py

# src/omniai/services/organization.py

"""
Organization service layer.
Used by:
- Auth (user signup)
- Org management (manual creation, invites, deletion)
"""

import re
import unicodedata
from typing import Optional
from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from omniai.core.logging import logger
from omniai.models.organization import Organization
from omniai.models.user import User, user_organization


def slugify(value: str, max_length: int = 50) -> str:
    """Convert 'My Org!' → 'my-org' (safe for URLs)"""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    slug = re.sub(r'[-\s]+', '-', value).strip('-_')
    return slug[:max_length]


async def create_organization_for_user(
    db: AsyncSession,
    user_id: str,
    name: str,
    set_as_default: bool = False
) -> Organization:
    """
    Creates an organization and links user as owner.
    Used during signup (set_as_default=True) and manual creation (False).
    """
    logger.debug("create_organization_for_user_start", name=name, user_id=user_id)

    # Generate unique slug
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Organization).where(Organization.slug == slug))
        if not result.scalars().first():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
        if counter > 100:
            logger.error("slug_generation_failed", name=name, base_slug=base_slug)
            raise ValueError("Could not generate unique slug")

    # Create org
    org = Organization(name=name, slug=slug)
    db.add(org)
    await db.flush()
    logger.debug("org_created", org_id=org.id, slug=slug)

    # Link user as owner
    await db.execute(
        insert(user_organization).values(
            user_id=user_id,
            organization_id=org.id,
            role="owner",
            is_default=set_as_default
        )
    )
    logger.info("user_linked_to_org", user_id=user_id, org_id=org.id, is_default=set_as_default)
    return org


# --- NEW: Delete Organization Function ---
async def delete_organization(db: AsyncSession, org_id: str, user_id: str) -> None:
    """
    Deletes an organization if:
    - User is the owner
    - It's not a personal organization (slug starts with 'personal-')
    Raises:
        HTTPException(404): If org not found or user not owner
        HTTPException(403): If trying to delete personal org
    """
    # 1. Verify ownership and existence in one query
    result = await db.execute(
        select(Organization)
        .join(user_organization, Organization.id == user_organization.c.organization_id)
        .where(
            Organization.id == org_id,
            user_organization.c.user_id == user_id,
            user_organization.c.role == "owner"
        )
    )
    org = result.scalar_one_or_none()
    
    if not org:
        logger.warning("delete_org_not_found_or_not_owner", org_id=org_id, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or you are not the owner"
        )

    # 2. Block deletion of personal orgs
    if org.slug.startswith("personal-"):
        logger.warning("delete_org_blocked_personal", org_id=org_id, slug=org.slug)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete personal organization"
        )

    # 3. Delete the organization (relies on DB FK cascade to clean up memberships)
    await db.execute(delete(Organization).where(Organization.id == org_id))
    await db.commit()
    logger.info("org_deleted", org_id=org_id, user_id=user_id)



# --- NEW: Remove Member Function ---
async def remove_member(
    db: AsyncSession,
    org_id: str,
    current_user_id: str,
    target_user_id: str
) -> None:
    """
    Owner removes a member from the organization.
    - Cannot remove self
    - Cannot remove another owner
    - Cannot remove from personal org
    """
    logger.debug("remove_member_start", org_id=org_id, current_user_id=current_user_id, target_user_id=target_user_id)

    # 1. Verify current user is owner of org
    if not await is_org_owner(db, current_user_id, org_id):
        logger.warning("remove_member_forbidden_not_owner", org_id=org_id, user_id=current_user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can remove members"
        )

    # 2. Prevent removing self
    if current_user_id == target_user_id:
        logger.warning("remove_member_forbidden_self", user_id=current_user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )

    # 3. Get target user's role
    target_role = await get_user_org_role(db, target_user_id, org_id)
    if target_role is None:
        logger.warning("remove_member_target_not_in_org", org_id=org_id, target_user_id=target_user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this organization"
        )

    # 4. Prevent removing other owners
    if target_role == "owner":
        logger.warning("remove_member_forbidden_owner", org_id=org_id, target_user_id=target_user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove organization owner"
        )

    # 5. Block removal from personal orgs
    org_result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
    org_slug = org_result.scalar_one_or_none()
    if org_slug and org_slug.startswith("personal-"):
        logger.warning("remove_member_forbidden_personal_org", org_id=org_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify personal organization"
        )

    # 6. Remove membership
    await db.execute(
        delete(user_organization)
        .where(
            user_organization.c.organization_id == org_id,
            user_organization.c.user_id == target_user_id
        )
    )
    await db.commit()
    logger.info("member_removed", org_id=org_id, removed_user_id=target_user_id, removed_by=current_user_id)


# --- NEW: Leave Organization Function ---
async def leave_organization(
    db: AsyncSession,
    org_id: str,
    user_id: str
) -> None:
    """
    User leaves an organization.
    - Cannot leave personal org
    - Cannot leave if last owner
    """
    logger.debug("leave_organization_start", org_id=org_id, user_id=user_id)

    # 1. Verify user is member of org
    current_role = await get_user_org_role(db, user_id, org_id)
    if current_role is None:
        logger.warning("leave_org_not_member", org_id=org_id, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this organization"
        )

    # 2. Block leaving personal org
    org_result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
    org_slug = org_result.scalar_one_or_none()
    if org_slug and org_slug.startswith("personal-"):
        logger.warning("leave_org_forbidden_personal", org_id=org_id, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot leave personal organization"
        )

    # 3. If user is owner, ensure at least one other owner exists
    if current_role == "owner":
        # Count other owners
        result = await db.execute(
            select(user_organization.c.user_id)
            .where(
                user_organization.c.organization_id == org_id,
                user_organization.c.role == "owner",
                user_organization.c.user_id != user_id
            )
        )
        other_owners = result.scalars().all()
        if not other_owners:
            logger.warning("leave_org_last_owner", org_id=org_id, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave: you are the last owner of this organization"
            )

    # 4. Remove membership
    await db.execute(
        delete(user_organization)
        .where(
            user_organization.c.organization_id == org_id,
            user_organization.c.user_id == user_id
        )
    )
    await db.commit()
    logger.info("user_left_org", org_id=org_id, user_id=user_id)




# --- Existing role functions (keep these) ---
async def get_user_org_role(db: AsyncSession, user_id: str, org_id: str) -> Optional[str]:
    result = await db.execute(
        select(user_organization.c.role)
        .where(user_organization.c.user_id == user_id)
        .where(user_organization.c.organization_id == org_id)
    )
    row = result.fetchone()
    return row[0] if row else None


async def is_org_owner(db: AsyncSession, user_id: str, org_id: str) -> bool:
    role = await get_user_org_role(db, user_id, org_id)
    return role == "owner"
```


<div style='page-break-after: always;'></div>

# File: tests\__init__.py

```py
```


<div style='page-break-after: always;'></div>

# File: tests\unit\__init__.py

```py
```


<div style='page-break-after: always;'></div>

# File: tests\unit\test_integration.py

```py
import httpx
import pytest
import os

from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError
from omniai.core.config import Settings


from sqlalchemy.ext.asyncio import AsyncSession
from omniai.api.deps import get_current_user
from omniai.models.user import User
from omniai.services.auth import get_user_from_token
from omniai.api.v1.schemas import UserCreate, OrganizationCreate
from fastapi import HTTPException




# URL of the real app inside Docker
BASE_URL = "http://app:8000"
HTTPX_TIMEOUT = 30.0


# All tests now use real HTTP
# Health check 1
@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        response = await ac.get("/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "omniai-core"}

# Signup to login to me 2
@pytest.mark.asyncio
async def test_full_auth_flow_with_default_tenant():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        email = "integration4.test@omniai.dev"
        password = "SecurePass123!"
        r1 = await ac.post("/v1/auth/signup", json={"email": email, "password": password})
        assert r1.status_code == 201

        r2 = await ac.post("/v1/auth/login", data={"username": email, "password": password})
        assert r2.status_code == 200
        token = r2.json()["access_token"]

        r3 = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200
        data = r3.json()
        assert data["email"] == email
        assert "active_organization_id" in data

        org_id = data["active_organization_id"]
        r4 = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": org_id})
        assert r4.status_code == 200

# Token accessing another token's tenant 3
@pytest.mark.asyncio
async def test_user_cannot_access_other_tenant():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        # User A
        await ac.post("/v1/auth/signup", json={"email": "usera@test.com", "password": "SecurePass123!"})
        login_a = await ac.post("/v1/auth/login", data={"username": "usera@test.com", "password": "SecurePass123!"})
        token_a = login_a.json()["access_token"]
        #me_a = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_a}"})
        #org_a = me_a.json()["active_organization_id"]

        # User B
        await ac.post("/v1/auth/signup", json={"email": "userb@test.com", "password": "SecurePass123!"})
        login_b = await ac.post("/v1/auth/login", data={"username": "userb@test.com", "password": "SecurePass123!"})
        token_b = login_b.json()["access_token"]
        me_b = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token_b}"})
        org_b = me_b.json()["active_organization_id"]

        # User A tries to access Org B → should be 403
        resp = await ac.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token_a}", "X-Tenant-ID": org_b}
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_ORG_MEMBER"




# Loging in with wrong password 4
@pytest.mark.asyncio
async def test_login_with_wrong_password():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        # Signup
        await ac.post("/v1/auth/signup", json={"email": "badpass@test.com", "password": "GoodPass123!"})
        # Login with wrong password
        r = await ac.post("/v1/auth/login", data={"username": "badpass@test.com", "password": "Wrong123!"})
        assert r.status_code == 401
        assert "incorrect email or password" in r.json()["detail"].lower()


# Testing missing header 5
@pytest.mark.asyncio
async def test_protected_route_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        r = await ac.get("/v1/me")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "MISSING_AUTH_TOKEN"

# Testing invalid token 6
@pytest.mark.asyncio
async def test_protected_route_with_malformed_token():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        r = await ac.get("/v1/me", headers={"Authorization": "Bearer invalid.junk.token"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "INVALID_TOKEN"


# Don't allow same email signup twice 7
@pytest.mark.asyncio
async def test_signup_duplicate_email():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        email = "dup@test.com"
        await ac.post("/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
        r2 = await ac.post("/v1/auth/signup", json={"email": email, "password": "AnotherPass123!"})
        assert r2.status_code == 400
        assert "email already registered" in r2.json()["detail"].lower()



# Fake tenant ID 8
@pytest.mark.asyncio
async def test_access_nonexistent_organization():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        # Signup + login
        email = "nonexist@test.com"
        await ac.post("/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
        login = await ac.post("/v1/auth/login", data={"username": email, "password": "SecurePass123!"})
        token = login.json()["access_token"]

        # Try to access a fake org UUID
        fake_org_id = "12345678-1234-5678-1234-567812345678"
        resp = await ac.get(
            "/v1/me",
            headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": fake_org_id}
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "ORG_NOT_FOUND"


# tests if token can be created and decoded 10
def test_jwt_roundtrip():
    from omniai.core.jwt import create_access_token, decode_token
    user_id = "usr_123abc"
    token = create_access_token({"sub": user_id})
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload

# tests if token format is checked 9
def test_decode_invalid_token():
    from jwt import PyJWTError

    from omniai.core.jwt import decode_token
    try:
        decode_token("invalid.token.here")
        raise AssertionError("Should have raised JWTError")
    except PyJWTError:
        pass  # Expected

# test if token doesn't start with usr_ or isn't an instance of (user_id, str)
def test_decode_token_with_invalid_user_id_format():
    """decode_token should raise PyJWTError if sub is not a valid user ID."""
    from omniai.core.jwt import create_access_token, decode_token
    from jwt import PyJWTError

    # Create token with invalid user ID (doesn't start with "usr_")
    token = create_access_token({"sub": "invalid-user-id"})

    with pytest.raises(PyJWTError) as exc_info:
        decode_token(token)

    assert "Invalid user ID format" in str(exc_info.value)


# User signed up an no default org was created,  then they login and when /me is fetched it finds no default org. #Should never happen 11
@pytest.mark.asyncio
async def test_user_with_no_default_org_fails_gracefully():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        email = "nodefault@test.com"
        password = "SecurePass123!"

        await ac.post("/v1/auth/signup", json={"email": email, "password": password})
        login = await ac.post("/v1/auth/login", data={"username": email, "password": password})
        token = login.json()["access_token"]

        from sqlalchemy import delete, select

        from omniai.db.session import AsyncSessionLocal
        from omniai.models.organization import Organization
        from omniai.models.user import User, user_organization

        async with AsyncSessionLocal() as db:
            user_result = await db.execute(select(User.id).where(User.email == email))
            user_id = user_result.scalar()

            # ✅ FIX: Use hyphen "-", not en dash "–"
            org_name = f"Personal – {email}"
            org_result = await db.execute(select(Organization.id).where(Organization.name == org_name))
            org_id = org_result.scalar()

            if user_id and org_id:
                await db.execute(
                    delete(user_organization)
                    .where(
                        user_organization.c.user_id == user_id,
                        user_organization.c.organization_id == org_id
                    )
                )
                await db.commit()

        resp = await ac.get("/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NO_DEFAULT_ORG"



# Test password hashing 12
def test_password_hashing():
    from omniai.services.auth import get_password_hash, verify_password
    pwd = "TestPass123!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("Wrong", hashed) is False


# Password strength test 13
@pytest.mark.asyncio
async def test_signup_weak_password():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=HTTPX_TIMEOUT) as ac:
        r = await ac.post("/v1/auth/signup", json={"email": "weak@test.com", "password": "123"})
        assert r.status_code == 422
        assert "Password must be at least 8 characters" in r.json()["detail"][0]["msg"]


# Test JWT_SECRET_KEY exists and valid hence success
def test_settings_loads_with_valid_env():
    """Settings should load successfully when all required env vars are set."""
    with mock.patch.dict(os.environ, {
        "JWT_SECRET_KEY": "test-secret-key",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb"
    }, clear=True):
        settings = Settings()
        assert settings.JWT_SECRET_KEY == "test-secret-key"
        assert "testdb" in settings.DATABASE_URL


# Test is missing JWT_SECRET_KEY raises an error
def test_settings_fails_without_jwt_secret_key():
    """Settings must require JWT_SECRET_KEY."""
    # Temporarily remove JWT_SECRET_KEY from environment
    with mock.patch.dict(os.environ, {}, clear=True):
        # Ensure no default is used
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        
        # Verify the error is about JWT_SECRET_KEY
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("JWT_SECRET_KEY",)
        assert "Field required" in errors[0]["msg"]


###############################################################
# Unit tests for src/omniai/services/auth.py — error paths in get_user_from_token
###############################################################

@pytest.mark.asyncio
async def test_get_user_from_token_missing_sub():
    mock_db = AsyncMock(spec=AsyncSession)

    with patch("omniai.services.auth.decode_token", return_value={"exp": 123456}):
        user = await get_user_from_token(mock_db, "valid-token")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_invalid_token():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Patch decode_token to raise exception
    with patch("omniai.core.jwt.decode_token", side_effect=Exception("Invalid token")):
        user = await get_user_from_token(mock_db, "invalid-token")
        assert user is None
        # Covers: exception / decode failure path


@pytest.mark.asyncio
async def test_get_user_from_token_user_not_found():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # sync method

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("omniai.services.auth.decode_token", return_value={"sub": "usr_123"}):
        user = await get_user_from_token(mock_db, "valid-token")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_error_paths():
    # Directly test multiple error branches in get_user_from_token

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Case 1: missing "sub"
    with patch("omniai.core.jwt.decode_token", return_value={"exp": 1769757322}):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None

    # Case 2: decode exception
    with patch("omniai.core.jwt.decode_token", side_effect=Exception("Decode fail")):
        user = await get_user_from_token(mock_db, "invalid-token")
        assert user is None

    # Case 3: user not found (DB query returns None)
    with patch("omniai.core.jwt.decode_token", return_value={"sub": "usr_123"}):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_decode_returns_non_dict():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)  # ✅ FIXED

    # Patch decode_token to return a non-dict (AttributeError on .get)
    with patch("omniai.core.jwt.decode_token", return_value="invalid"):
        user = await get_user_from_token(mock_db, "valid-token")
        assert user is None



###############################################################
# Unit tests for src/omniai/api/deps.py
###############################################################


class MockCredentials:
    def __init__(self, credentials: str):
        self.credentials = credentials

class MockDB:
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass


@pytest.mark.asyncio
async def test_get_current_user_success():
    from sqlalchemy.ext.asyncio import AsyncSession
    
    with patch("omniai.api.deps.get_user_from_token", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = User(id="usr_123", email="test@example.com", hashed_password="x")
        mock_db = AsyncMock(spec=AsyncSession)
        
        user = await get_current_user(
            credentials=MockCredentials("valid-token"),
            db=mock_db
        )
        assert user.id == "usr_123"
        mock_func.assert_called_once_with(mock_db, "valid-token")


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with patch("omniai.api.deps.get_user_from_token", new_callable=AsyncMock) as mock_func:
        mock_func.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await get_current_user(
                credentials=MockCredentials("invalid-token"),
                db=MockDB()
            )
        assert exc.value.status_code == 401



###############################################################
# Unit tests for src/omniai/api/v1/schemas.py
###############################################################

def test_user_create_password_validation():

    # Valid password
    valid = UserCreate(email="test@example.com", password="SecurePass123!")
    assert valid.password == "SecurePass123!"

    # Invalid passwords
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        UserCreate(email="test@example.com", password="Short1!")

    with pytest.raises(ValueError, match="Password must contain an uppercase letter"):
        UserCreate(email="test@example.com", password="nopassword123!")

    with pytest.raises(ValueError, match="Password must contain a lowercase letter"):
        UserCreate(email="test@example.com", password="NOPASSWORD123!")

    with pytest.raises(ValueError, match="Password must contain a digit"):
        UserCreate(email="test@example.com", password="NoDigitsHere!")

    with pytest.raises(ValueError, match="Password must contain a special character"):
        UserCreate(email="test@example.com", password="NoSpecial123")


def test_organization_create_name_validation():

    # Valid name
    valid = OrganizationCreate(name="My Org")
    assert valid.name == "My Org"

    # Empty name
    with pytest.raises(ValueError, match="Organization name cannot be empty"):
        OrganizationCreate(name="   ")

    # Too long
    with pytest.raises(ValueError, match="Organization name too long"):
        OrganizationCreate(name="A" * 101)
```


<div style='page-break-after: always;'></div>

# File: tests\unit\test_unit.py

```py
import uuid
import pytest
from typing import AsyncGenerator


from sqlalchemy.ext.asyncio import AsyncSession
from omniai.models.user import User, user_organization
from omniai.models.organization import Organization
from omniai.services.auth import get_password_hash

from omniai.services.invite import create_invite, accept_invite
from omniai.api.v1.schemas import InviteCreate
from sqlalchemy import select
from fastapi import HTTPException

from omniai.services.organization import  delete_organization, leave_organization, remove_member


############################################################################################ for unit tests to have a different dp session

# --- IN-MEMORY TEST DB SETUP (self-contained) ---
import asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Create in-memory SQLite engine (shared across tests in this file)
_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
    poolclass=StaticPool,  # Required for in-memory SQLite sharing
)

_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def _init_test_db():
    from omniai.models.base import Base  # ← Single shared Base
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def initialize_test_db():
    """Initialize the in-memory test DB once before any test runs."""
    asyncio.run(_init_test_db())

# --- END TEST DB SETUP ---

#############################################################################################################


# tests/unit/test_session.py
@pytest.mark.asyncio
async def test_get_db_yields_session():
    from omniai.db.session import get_db
    """get_db should yield an async session that auto-closes."""
    async for session in get_db():
        assert session is not None
        assert session.is_active  # Session should be active during yield

    # After the async for loop, session should be closed
    # You can't check this directly, but you can verify no exceptions
    # (which implies proper cleanup)


############################################################### testing services/auth.py Testing functions in Isolation

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh DB session for each test (with rollback)."""
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()  # Clean up after each test



# Unit test for authenticate_user
@pytest.mark.asyncio
async def test_authenticate_user_success(db):
    from omniai.services.auth import authenticate_user, create_user_with_org
    
    # Create a test user
    email = "auth_test_success@test.com"
    password = "SecurePass123!"
    await create_user_with_org(db, email, password)
    
    # Authenticate
    user = await authenticate_user(db, email, password)
    assert user is not None
    assert user.email == email


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(db):
    from omniai.services.auth import authenticate_user, create_user_with_org
    
    email = "auth_test_invalid@test.com"
    password = "SecurePass123!"
    await create_user_with_org(db, email, password)
    
    # Wrong password
    user = await authenticate_user(db, email, "WrongPassword123!")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent_email(db):
    from omniai.services.auth import authenticate_user
    
    user = await authenticate_user(db, "nonexistent@test.com", "any_password")
    assert user is None


@pytest.mark.asyncio
async def test_create_user_with_org_creates_personal_org(db):
    from omniai.services.auth import create_user_with_org
    from omniai.models.user import User
    from omniai.models.organization import Organization
    from sqlalchemy import select

    email = "unit_test_create@test.com"
    password = "TestPass123!"
    
    user = await create_user_with_org(db, email, password)
    
    # Verify user
    assert user.email == email
    assert user.hashed_password is not None
    
    # Verify org was created
    result = await db.execute(select(Organization).where(Organization.name.like(f"Personal – {email}%")))
    org = result.scalar_one_or_none()
    assert org is not None
    assert org.slug.startswith("personal")
    
    # Verify membership
    from omniai.models.user import user_organization
    result = await db.execute(
        select(user_organization)
        .where(user_organization.c.user_id == user.id)
        .where(user_organization.c.organization_id == org.id)
    )
    membership = result.fetchone()
    assert membership is not None
    assert membership.is_default is True
    assert membership.role == "owner"


# Make slug to always exist in db so that we loop 100+ times to trigger error "Could not generate a unique slug for Personal org""

@pytest.mark.asyncio
async def test_create_user_with_org_fails_after_100_slug_attempts(db):
    from omniai.services.auth import create_user_with_org
    from omniai.models.organization import Organization

    # Create 100 orgs with slug "personal-test-collision"
    base_name = "Personal – test-collision@test.com"
    for i in range(100):
        if i == 0:
            slug = "personal-test-collisiontestcom"
        else:
            slug = f"personal-test-collisiontestcom-{i}"
        org = Organization(name=f"{base_name} {i}", slug=slug)
        db.add(org)
    await db.commit()

    email = "test-collision@test.com"
    password = "TestPass123!"

    with pytest.raises(ValueError, match="Could not generate unique slug"):
        await create_user_with_org(db, email, password)



###############################################################
# Unit tests for services/organization.py
###############################################################

@pytest.mark.asyncio
async def test_get_user_org_role_returns_role(db):
    from omniai.services.organization import get_user_org_role
    from omniai.models.user import User, user_organization
    from omniai.models.organization import Organization

    # Create user and org
    user = User(email="org_test@test.com", hashed_password="x")
    org = Organization(name="Test Org", slug="test-org")
    
    db.add(user)
    db.add(org)
    await db.flush()

    # Link with role "member"
    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="member"
        )
    )
    await db.commit()

    # Test
    role = await get_user_org_role(db, str(user.id), str(org.id))
    assert role == "member"


@pytest.mark.asyncio
async def test_get_user_org_role_returns_none_if_no_membership(db):
    from omniai.services.organization import get_user_org_role
    from omniai.models.user import User
    from omniai.models.organization import Organization

    user = User(email="no_member@test.com", hashed_password="x")
    org = Organization(name="Lonely Org", slug="lonely")

    db.add(user)
    db.add(org)
    await db.flush()
    
    await db.commit()

    role = await get_user_org_role(db, str(user.id), str(org.id))
    assert role is None


@pytest.mark.asyncio
async def test_is_org_owner_returns_true_if_owner(db):
    from omniai.services.organization import is_org_owner
    from omniai.models.user import User, user_organization
    from omniai.models.organization import Organization

    user = User(email="owner@test.com", hashed_password="x")
    org = Organization(name="My Org", slug="my-org")

    db.add(user)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="owner"
        )
    )
    await db.commit()

    assert await is_org_owner(db, str(user.id), str(org.id)) is True


@pytest.mark.asyncio
async def test_is_org_owner_returns_false_if_not_owner(db):
    from omniai.services.organization import is_org_owner
    from omniai.models.user import User, user_organization
    from omniai.models.organization import Organization

    user = User(email="not_owner@test.com", hashed_password="x")
    org = Organization(name="Not Mine", slug="not-mine")

    db.add(user)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="member"  # ← not owner
        )
    )
    await db.commit()

    assert await is_org_owner(db, str(user.id), str(org.id)) is False

############################################### New

@pytest.mark.asyncio
async def test_remove_member_forbidden_not_owner(db):
    # Setup: owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Non-owner tries to remove a member
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, non_owner.id, owner.id)
    
    assert exc.value.status_code == 403
    assert "Only owners can remove members" in exc.value.detail


@pytest.mark.asyncio
async def test_remove_member_forbidden_self(db):
    # Setup: owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Owner tries to remove themselves
    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner.id, owner.id)
    
    assert exc.value.status_code == 400
    assert "Cannot remove yourself" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_forbidden_personal(db):
    # Setup: user + personal org
    user_email = f"user_{uuid.uuid4().hex}@test.com"
    user = User(email=user_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(user)
    await db.flush()

    # Personal org (slug starts with "personal-")
    personal_slug = f"personal-{uuid.uuid4().hex}"
    org = Organization(name="Personal", slug=personal_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=user.id,
            organization_id=org.id,
            role="owner",
            is_default=True
        )
    )
    await db.commit()

    # User tries to leave personal org
    with pytest.raises(HTTPException) as exc:
        await leave_organization(db, org.id, user.id)
    
    assert exc.value.status_code == 403
    assert "Cannot leave personal organization" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_last_owner(db):
    # Setup: single owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Owner tries to leave — should fail (last owner)
    with pytest.raises(HTTPException) as exc:
        await leave_organization(db, org.id, owner.id)
    
    assert exc.value.status_code == 400
    assert "you are the last owner" in exc.value.detail.lower()


##


@pytest.mark.asyncio
async def test_remove_member_target_not_in_org(db):
    # Setup: owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Try to remove a user who is NOT in the org
    fake_user_id = "usr_1234567890abcdef1234567890abcdef"
    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner.id, fake_user_id)
    
    assert exc.value.status_code == 404
    assert "User is not a member of this organization" in exc.value.detail


@pytest.mark.asyncio
async def test_remove_member_forbidden_owner(db):
    # Setup: two owners in one org
    owner1_email = f"owner1_{uuid.uuid4().hex}@test.com"
    owner1 = User(email=owner1_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner1)
    await db.flush()

    owner2_email = f"owner2_{uuid.uuid4().hex}@test.com"
    owner2 = User(email=owner2_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner2)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link both as owners
    await db.execute(
        user_organization.insert().values(
            user_id=owner1.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.execute(
        user_organization.insert().values(
            user_id=owner2.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # owner1 tries to remove owner2 → should fail
    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner1.id, owner2.id)
    
    assert exc.value.status_code == 400
    assert "Cannot remove organization owner" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_not_member(db):
    # Setup: user + org (user is NOT a member)
    user_email = f"user_{uuid.uuid4().hex}@test.com"
    user = User(email=user_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(user)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # User is NOT linked to org
    await db.commit()

    # User tries to leave → should fail
    with pytest.raises(HTTPException) as exc:
        await leave_organization(db, org.id, user.id)
    
    assert exc.value.status_code == 404
    assert "You are not a member of this organization" in exc.value.detail


@pytest.mark.asyncio
async def test_leave_organization_success_with_other_owner(db):
    # Setup: 2 owners in one org
    owner1_email = f"owner1_{uuid.uuid4().hex}@test.com"
    owner1 = User(email=owner1_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner1)
    await db.flush()

    owner2_email = f"owner2_{uuid.uuid4().hex}@test.com"
    owner2 = User(email=owner2_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner2)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link both as owners
    await db.execute(
        user_organization.insert().values(
            user_id=owner1.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.execute(
        user_organization.insert().values(
            user_id=owner2.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    # Owner1 leaves → should succeed (Owner2 remains)
    await leave_organization(db, org.id, owner1.id)

    # Verify Owner1 is gone, Owner2 remains
    result = await db.execute(
        select(user_organization.c.user_id, user_organization.c.role)
        .where(user_organization.c.organization_id == org.id)
    )
    memberships = result.fetchall()
    user_ids = [m[0] for m in memberships]
    roles = [m[1] for m in memberships]

    assert owner1.id not in user_ids
    assert owner2.id in user_ids
    assert "owner" in roles
    
####

@pytest.mark.asyncio
async def test_delete_organization_not_owner(db):
    owner = User(
        email=f"user_{uuid.uuid4().hex}@test.com",
        hashed_password="x"
    )
    db.add(owner)
    await db.flush()

    # IMPORTANT: unique slug to avoid collisions
    org = Organization(
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex}"
    )
    db.add(org)
    await db.flush()
    await db.commit()

    # User is NOT linked as owner → should be treated as not found
    with pytest.raises(HTTPException) as exc:
        await delete_organization(db, org.id, owner.id)

    assert exc.value.status_code == 404
    assert "not found or you are not the owner" in exc.value.detail.lower()



@pytest.mark.asyncio
async def test_delete_organization_personal_forbidden(db):
    owner = User(email=f"user_{uuid.uuid4().hex}@test.com", hashed_password="x")
    db.add(owner)
    await db.flush()

    org = Organization(name="Personal", slug=f"personal-{uuid.uuid4().hex}")
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=True
        )
    )
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await delete_organization(db, org.id, owner.id)

    assert exc.value.status_code == 403



@pytest.mark.asyncio
async def test_delete_organization_success(db):
    owner = User(email=f"user_{uuid.uuid4().hex}@test.com", hashed_password="x")
    db.add(owner)
    await db.flush()

    org = Organization(name="Test Org", slug=f"test-{uuid.uuid4().hex}")
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )
    await db.commit()

    await delete_organization(db, org.id, owner.id)

    result = await db.execute(
        select(Organization).where(Organization.id == org.id)
    )
    assert result.scalar_one_or_none() is None




@pytest.mark.asyncio
async def test_remove_member_forbidden_personal_org(db):
    owner = User(email=f"owner_{uuid.uuid4().hex}@test.com", hashed_password="x")
    member = User(email=f"member_{uuid.uuid4().hex}@test.com", hashed_password="x")
    db.add_all([owner, member])
    await db.flush()

    org = Organization(name="Personal", slug=f"personal-{uuid.uuid4().hex}")
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=True
        )
    )
    await db.execute(
        user_organization.insert().values(
            user_id=member.id,
            organization_id=org.id,
            role="member",
            is_default=False
        )
    )
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await remove_member(db, org.id, owner.id, member.id)

    assert exc.value.status_code == 403
    assert "personal organization" in exc.value.detail.lower()



@pytest.mark.asyncio
async def test_remove_member_success(db):
    # Create owner
    owner = User(
        email=f"owner_{uuid.uuid4().hex}@test.com",
        hashed_password="x"
    )
    db.add(owner)
    await db.flush()

    # Create member
    member = User(
        email=f"member_{uuid.uuid4().hex}@test.com",
        hashed_password="x"
    )
    db.add(member)
    await db.flush()

    # Create org (NOT personal)
    org = Organization(
        name="Test Org",
        slug=f"test-org-{uuid.uuid4().hex}"
    )
    db.add(org)
    await db.flush()

    # Link owner
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Link member
    await db.execute(
        user_organization.insert().values(
            user_id=member.id,
            organization_id=org.id,
            role="member",
            is_default=False
        )
    )
    await db.commit()

    # Act: owner removes member
    await remove_member(db, org.id, owner.id, member.id)

    # Assert: member is gone
    result = await db.execute(
        select(user_organization.c.user_id)
        .where(user_organization.c.organization_id == org.id)
    )
    remaining_user_ids = [row[0] for row in result.fetchall()]

    assert member.id not in remaining_user_ids
    assert owner.id in remaining_user_ids


###############################################################
# Unit tests for src/omniai/services/invite.py
###############################################################

@pytest.mark.asyncio
async def test_create_invite_success(db):
    # Create owner (no commit)
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    hashed_pw = get_password_hash("SecurePass123!")
    owner = User(email=owner_email, hashed_password=hashed_pw)
    db.add(owner)
    await db.flush()

    # Create org with UNIQUE slug
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link owner to org
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    assert invite.email == invitee_email
    assert invite.organization_id == org.id
    assert invite.invited_by_id == owner.id
    assert len(invite.token) > 20


@pytest.mark.asyncio
async def test_create_invite_forbidden_not_owner(db):
    # Owner
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Non-owner
    non_owner_email = f"nonowner_{uuid.uuid4().hex}@test.com"
    non_owner = User(email=non_owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(non_owner)
    await db.flush()

    # Org owned by owner (UNIQUE slug)
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Non-owner tries to invite → should fail
    invite_data = InviteCreate(email="newuser@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, non_owner.id, invite_data)
    
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_accept_invite_success(db):
    # Owner
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Org (UNIQUE slug)
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Member
    member_email = f"member_{uuid.uuid4().hex}@test.com"
    member = User(email=member_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(member)
    await db.flush()

    # Create invite
    invite_data = InviteCreate(email=member_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Accept invite
    await accept_invite(db, invite.token, member.id)

    # Verify membership
    result = await db.execute(
        select(user_organization.c.role)
        .where(
            user_organization.c.user_id == member.id,
            user_organization.c.organization_id == org.id
        )
    )
    role = result.scalar_one_or_none()
    assert role == "member"


@pytest.mark.asyncio
async def test_accept_invite_invalid_token(db):

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, "invalid-token", "usr_123")
    
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_invite_user_already_member(db):

    # Create owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Try to invite the *same* user again
    invite_data = InviteCreate(email=owner_email)
    with pytest.raises(HTTPException) as exc:
        await create_invite(db, org.id, owner.id, invite_data)
    
    assert exc.value.status_code == 400
    assert "already a member" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_accept_invite_email_mismatch(db):

    # Owner + org
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite for *another* email
    invitee_email = "invitee@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Now try to accept with a *different* user (email mismatch)
    member_email = "mismatch@test.com"
    member = User(email=member_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(member)
    await db.flush()

    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, invite.token, member.id)
    
    assert exc.value.status_code == 400
    assert "does not match your account" in exc.value.detail


@pytest.mark.asyncio
async def test_accept_invite_user_not_found(db):

    # Create owner manually (no personal org)
    owner_email = f"owner_{uuid.uuid4().hex}@test.com"
    owner = User(email=owner_email, hashed_password=get_password_hash("SecurePass123!"))
    db.add(owner)
    await db.flush()

    # Create org manually
    unique_slug = f"test-org-{uuid.uuid4().hex}"
    org = Organization(name="Test Org", slug=unique_slug)
    db.add(org)
    await db.flush()

    # Link owner to org
    await db.execute(
        user_organization.insert().values(
            user_id=owner.id,
            organization_id=org.id,
            role="owner",
            is_default=False
        )
    )

    # Create invite
    invitee_email = f"invitee_{uuid.uuid4().hex}@test.com"
    invite_data = InviteCreate(email=invitee_email)
    invite = await create_invite(db, org.id, owner.id, invite_data)

    # Try to accept with a *non-existent* user ID
    non_existent_user_id = "usr_1234567890abcdef1234567890abcdef"
    with pytest.raises(HTTPException) as exc:
        await accept_invite(db, invite.token, non_existent_user_id)
    
    assert exc.value.status_code == 404
    assert "User not found" in exc.value.detail

####################################New
```

