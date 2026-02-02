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