# OMNIAI Core Platform

> The sovereign, production-grade foundation for AI systems that serve 1 billion underserved people.

> Built for performance, reliability, and African problem-solving  
> From Nakuru, with hunger and code  

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

```bash
git clone https://github.com/ahooTech/omniai-core.git  
cd omniai-core
python -m venv venv
source venv/Scripts/activate .  # Linux/Mac
# venv\Scripts\activate  # Windows

pip install -e .
uvicorn src.omniai.main:app --reload
```
## 📁 Project Structure
```
OMNIAI-CORE/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitattributes
├── .gitignore
├── LICENSE
├── README.md
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── scripts/
│   └── bootstrap.sh
├── src/
│   ├── omniai/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── agriculture.py
│   │   │       └── health.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── middleware.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── organization.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── organization.py
│   └── omniai.egg-info/
│       ├── dependency_links.txt
│       ├── PKG-INFO
│       ├── SOURCES.txt
│       ├── top_level.txt
│       └── ... (other standard egg-info files — **no entry_points.txt**)
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       └── test_tenant_middleware.py
└── venv/
    ├── Include/
    ├── Lib/
    ├── Scripts/
    └── pyvenv.cfg
```
## 🧪 Testing

```bash
pytest tests/unit/test_tenant_middleware.py -v
```

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


# https://github.com/ahooTech/omniai-core.git

