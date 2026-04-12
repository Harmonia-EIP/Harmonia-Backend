# Harmonia Backend API

A modern **FastAPI authentication backend** with JWT-based authentication, user profiles, and PostgreSQL integration.
Designed for **scalable frontend integration** (mobile & web).

---

## 🔗 Links

* 🌐 API Base URL: `https://harmonia-backend-production-2c25.up.railway.app`
* 📚 API Docs (Swagger): `https://harmonia-backend-production-2c25.up.railway.app/docs`
* 📦 EIP Repository: `https://github.com/Harmonia-EIP`

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

pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 🔧 Installation

### 1. Clone repository

```bash
git clone https://github.com/Harmonia-EIP/Harmonia-Backend.git
cd Harmonia-Backend
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

`.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/harmoniadatabase
JWT_SECRET=your_super_secret_key_here
ACCESS_TOKEN_EXPIRE_HOURS=24
ALGORITHM=HS256
```

---

## 🏃 Running the Server

```bash
uvicorn main:app --reload
```


## 📊 Architecture & Diagrams

### 🗄️ Database Diagram

![Database Diagram](docs/diagram-db.png)

---

### 🧱 Class Diagram

![Class Diagram](docs/diagram-class-backend.png)


---

## 📦 Dependencies

```
fastapi==0.103.2
uvicorn[standard]==0.23.2

pydantic==2.4.2
pydantic-settings==2.0.3

sqlalchemy==2.0.23
psycopg2-binary==2.9.9

passlib[bcrypt]==1.7.4
bcrypt==4.0.1

python-jose[cryptography]==3.3.0

python-dotenv==1.0.0
requests==2.31.0
httpx==0.25.2

email-validator==2.1.0.post1
```

---

## 🚀 Deployment

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📝 License

EIP Project - Epitech 2027

---

## 👥 Support

For issues or contributions, open a GitHub issue or pull request.
