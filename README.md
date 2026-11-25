# Harmonia Backend API

A modern **FastAPI authentication backend** with JWT-based authentication, user profiles, and PostgreSQL integration.
Designed for **scalable frontend integration** (mobile & web).

---

## 🔗 Links

* 🌐 API Base URL: https://harmonia-backend-production-2c25.up.railway.app
* 📚 API Docs (Swagger): https://harmonia-backend-production-2c25.up.railway.app/docs
* 📦 EIP Repository: https://github.com/Harmonia-EIP

---

## 🚀 Features

* 🔐 **Secure Authentication** (Signup / Signin with bcrypt hashing)
* 🎟️ **JWT Token Management** (24h expiration)
* 👤 **User Profiles**
* ⚠️ **Custom Exception Handling**
* 🗄️ **PostgreSQL + SQLAlchemy ORM**
* ✅ **Email Validation (Pydantic)**

---

## 📋 Requirements

* Python **3.10+**
* PostgreSQL **12+**

---

## ⚡ Quick Start

```bash
git clone https://github.com/Harmonia-EIP/Harmonia-Backend.git
cd Harmonia-Backend

pip install -r requirements-dev.txt
python migrate.py                          # crée / met à jour le schéma
SEED_TEST_USERS=1 python -m seed_initial_data   # rôles + comptes de test (dev uniquement)
uvicorn main:app --reload
```

---

## 🔧 Configuration

`.env` :

```env
DATABASE_URL=postgresql://user:password@localhost:5432/harmoniadatabase
# Obligatoire, 32 caractères minimum, sinon l'API refuse de démarrer.
# Générer : python -c "import secrets; print(secrets.token_urlsafe(48))"
JWT_SECRET=
ACCESS_TOKEN_EXPIRE_HOURS=24
ALGORITHM=HS256
AI_URL=http://localhost:5000

# Optionnel
CORS_ORIGINS=http://localhost:5173
PUBLIC_BASE_URL=https://api.example.com   # URL publique (liens d'avatars)
UPLOAD_DIR=uploads
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=1
FORWARDED_ALLOW_IPS=*          # IP du reverse proxy autorisée à fixer X-Forwarded-For
SEED_TEST_USERS=0              # 1 = crée admin/staff/user de test. JAMAIS en production
```

---

## 🗄️ Base de données (Alembic)

Le schéma est géré par Alembic (`migrations/`), plus par `create_all`.

```bash
python migrate.py                              # à jour (lancé par entrypoint.sh)
alembic revision -m "add something"            # nouvelle migration, à éditer
```

`migrate.py` détecte une base créée avant Alembic et la marque au schéma
initial (`0001`) avant d'appliquer les migrations suivantes.

---

## 🛡️ Sécurité

* Les comptes désactivés ne peuvent plus utiliser l'API (403 `NO_PERMISSION`).
* Changer de mot de passe révoque tous les tokens existants :
  `PUT /profile/me/password` renvoie le nouveau `token`.
* Login : réponse identique (401) que le compte existe ou non.
* Limitation de débit en mémoire (429 `RATE_LIMITED` + `Retry-After`) sur le login,
  l'inscription, les changements d'email / mot de passe et l'IA.
* Emails et pseudos uniques sans tenir compte de la casse.

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest
ruff check . && ruff format .
```

En CI, `ruff format` est appliqué automatiquement et commité sur la branche de la PR.

---

## 📊 Architecture & Diagrams

### 🗄️ Database Diagram

![Database Diagram](docs/diagram-db.png)

---

### 🧱 Class Diagram

![Class Diagram](docs/diagram-class-backend.png)


---

## 📦 Dependencies

Voir `requirements.txt` (production) et `requirements-dev.txt` (tests, lint).

---

## 🚀 Deployment

Push sur `main` → `.github/workflows/deploy-vps.yml` : `git pull` sur le VPS puis
`docker compose up -d --build --wait`. Le conteneur attend la base, lance les
migrations puis le seed des rôles, et démarre uvicorn sous un utilisateur non-root.
Le healthcheck Docker interroge `GET /health`.

---

## 📝 License

EIP Project - Epitech 2027

---

## 👥 Support

For issues or contributions, open a GitHub issue or pull request.
