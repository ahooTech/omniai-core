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