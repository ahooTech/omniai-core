
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