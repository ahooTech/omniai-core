
```markdown
# [ADR-001] Use PostgreSQL as Primary Database with Application-Level Multi-Tenancy

## Status
✅ Accepted

## Context
OMNIAI Core requires a production-grade relational database to store:
- User identities (email, password hash)
- Organization memberships with role and default status
- Multi-tenancy context for all API operations

Key requirements:
- **Strong consistency** for authentication and tenant isolation
- **Efficient querying** of user-org relationships (including "default org" per user)
- **Scalable indexing** for high-concurrency auth and org-switching
- **Future support for Row-Level Security (RLS)**
- **Operational simplicity** for cloud deployment (Render, AWS, GCP)

## Decision
We select **PostgreSQL 15+** as the primary database and implement:
- A normalized schema using SQLAlchemy 2.0 declarative models
- An explicit many-to-many `user_organization` association table with metadata
- Strategic indexes, including a **partial unique index** to enforce one default org per user
- Human-readable prefixed IDs (`usr_...`, `org_...`) for debugging and auditability

### Schema Design (Actual Implementation)

#### `users` Table
- `id`: `TEXT` primary key, default `"usr_" + uuid4().hex`
- `email`: unique, indexed
- `hashed_password`: bcrypt hash
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

### Indexing Strategy
- `users(email)` → O(1) login lookup
- `organizations(slug)` → org resolution by URL
- `user_organization(user_id)` → list user’s orgs
- `user_organization(organization_id)` → list org members
- **Partial index on `(user_id)` where `is_default = true`** → enforce default org uniqueness

## Consequences

### Good
- **Data integrity**: Foreign keys and partial index prevent invalid states (e.g., two default orgs)
- **Debuggability**: Prefixed IDs (`usr_...`, `org_...`) are human-readable in logs
- **Flexibility**: `role` and `is_default` in association table avoid extra joins
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
- Render PostgreSQL: https://render.com/docs/databases/postgres
```