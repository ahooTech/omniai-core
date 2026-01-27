
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