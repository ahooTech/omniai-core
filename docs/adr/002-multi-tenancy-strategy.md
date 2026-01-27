
```markdown
# [ADR-002] Multi-Tenancy via Application-Level Context with Default Org Enforcement

## Status
✅ Accepted

## Context
OMNIAI Core must support:
- Users belonging to **multiple organizations simultaneously**
- Each user having a **single active (default) organization** at any time
- **Strict data isolation**: no cross-tenant data leakage
- **Role-based permissions**: `owner` (can delete org) vs `member` (can only leave)
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

#### 3. Data Isolation Enforcement
- All service/repository methods accept `current_org_id`
- Database queries include:  
  ```python
  db.query(Model).filter(Model.org_id == current_org_id)
  ```
- No global queries allowed — enforced by code review and testing

#### 4. Default Organization Logic
- On signup: auto-create personal org `Personal – {email}` with `is_default=true`
- User can switch default org via profile update (client calls `PATCH /v1/users/me`)
- First joined org becomes default if none exists

#### 5. Role-Based Access Control (RBAC)
- Middleware attaches `role` to request context
- Endpoints check role before sensitive operations:
  - Only `owner` can delete org or remove other members
  - `member` can only leave org

## Consequences

### Good
- **Strong isolation**: App-layer filtering prevents accidental cross-tenant access
- **Flexible membership**: Users can join thousands of orgs without schema changes
- **Audit-ready**: Every log entry includes `org_id` and `user_id`
- **Client-controlled UX**: Frontend manages active org via header
- **Future-proof**: Can layer PostgreSQL RLS as defense-in-depth later

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
- Middleware: [`middleware.py`](https://github.com/ahooTech/omniai-core) (tenant validation + context binding)
- Render Deployment: https://omniai-web.onrender.com
```