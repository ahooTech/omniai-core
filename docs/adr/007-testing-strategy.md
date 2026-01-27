# [ADR-007] Isolated, High-Coverage Testing Strategy with CI Quality Gates

## Status
✅ Accepted

## Context
OMNIAI Core must maintain **extreme reliability** because:
- It handles sensitive user data (email, passwords, org memberships)
- Multi-tenancy logic is complex (default org, roles, isolation)
- Auth and tenant validation are security-critical
- Future AI agents will depend on this foundation

Requirements:
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

#### 2. Test Structure
- **Unit tests**: Pure functions (e.g., password hashing, slug generation)
- **Integration tests**:  
  - Auth flow: signup → login → access `/me`  
  - Org flow: create org → invite user → switch default org  
  - Tenant isolation: verify user A can’t see org B
- **Fixtures**:  
  - `test_user`, `test_org`, `auth_headers` → reusable test data
- **Async support**: `pytest-asyncio` for async endpoint tests

#### 3. Coverage Enforcement
- **Tool**: `pytest-cov`
- **Threshold**: Fail if coverage < 90%
- **Report**: HTML coverage report saved as CI artifact
- **Focus areas**:  
  - `services/` (auth, org logic) → 100% covered  
  - `api/` (routers) → >90% covered  
  - Excludes: `main.py`, migrations

#### 4. CI Quality Gates (GitHub Actions)
- **Pipeline**:
  1. Run unit + integration tests
  2. Measure coverage → fail if <90%
  3. Run linter (`ruff`)
  4. Run type checker (`mypy`)
  5. Run security scanner (`bandit`, `safety`)
- **Policy**: Any step failure = deployment blocked
- **Speed**: Tests complete in <90 seconds (optimized DB setup)

#### 5. No Mocking Policy
- **Why**: Mocking hides integration bugs (e.g., SQL syntax errors, constraint violations)
- **What we test against**:
  - Real PostgreSQL (via Docker in CI)
  - Real SQLAlchemy async engine
  - Real FastAPI test client
- **Exception**: External HTTP calls (e.g., SMS APIs) → mocked

## Consequences

### Good
- **Zero test pollution**: Parallel test runs safe
- **High confidence**: Critical paths (auth, tenant isolation) fully covered
- **Security assurance**: Auth logic tested against real attack vectors
- **CI as gatekeeper**: No broken code reaches production
- **Debuggable**: Real DB errors surface immediately

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