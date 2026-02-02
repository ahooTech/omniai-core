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


