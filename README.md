# Harmonia Backend API

A modern **FastAPI authentication backend** with JWT-based authentication, user profiles, and PostgreSQL database integration. Built for seamless integration with frontend applications.

---

## 🚀 Features

- **User Authentication**: Secure signup and signin with bcrypt password hashing
- **JWT Token Management**: 24-hour access tokens with automatic expiration
- **User Profiles**: Retrieve authenticated user information
- **Custom Exception Handling**: Comprehensive error responses with proper HTTP status codes
- **Database Integration**: SQLAlchemy ORM with PostgreSQL
- **Email Validation**: Built-in email validation using Pydantic
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

---

## 📋 Requirements

- Python **3.10+**
- PostgreSQL **12+**

---

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Harmonia-Backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirement.txt
   ```

3. **Configure environment variables** in `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/harmoniadatabase
   JWT_SECRET=your_secret_key_here
   ```

---

## 🏃 Running the Server

**Development mode** (with auto-reload):
```bash
uvicorn main:app --reload
```

**Custom host and port**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

**Production mode**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs` (Swagger UI)

---

## 📁 Project Structure

```
.
├── main.py                          # Application entry point
├── .env                             # Environment variables (not in git)
├── .gitignore                       # Git ignore rules
├── requirement.txt                  # Python dependencies
│
├── api/
│   └── auth.py                      # /auth endpoints (signup, signin)
│
├── services/
│   └── auth_service.py              # Signup/Signin business logic
│
├── utils/
│   └── jwt_handler.py               # JWT token creation & validation
│
├── models/
│   └── response_model.py            # Response schemas
│
└── README.md
```

---

## 📡 API Endpoints

### Authentication

**POST** `/auth/signup`
- Register a new user
- **Request**:
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securePassword123"
  }
  ```
- **Response** (201):
  ```json
  {
    "message": "User created successfully",
    "user_id": 1,
    "token": "eyJhbGc..."
  }
  ```

**POST** `/auth/signin`
- Login with email or username
- **Request**:
  ```json
  {
    "identifier": "johndoe@example.com",
    "password": "securePassword123"
  }
  ```
- **Response** (200):
  ```json
  {
    "message": "Login successful",
    "user_id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "token": "eyJhbGc..."
  }
  ```

---

## 🔐 Authentication

The API uses **JWT (JSON Web Tokens)** for authentication:

1. **Signup** or **Signin** returns an access token valid for **24 hours**
2. Include token in subsequent requests using the `Authorization` header:
   ```
   Authorization: Bearer eyJhbGc...
   ```
3. Tokens are validated server-side and automatically expire after 24 hours

---

## ⚙️ Configuration

Edit `.env` to customize:

```env
# Database connection string
DATABASE_URL=postgresql://user:password@host:port/database

# JWT secret key (use a strong random string in production)
JWT_SECRET=your_super_secret_key_here

# Access token expire hours time
ACCESS_TOKEN_EXPIRE_HOURS=24

# Algorithm of the cryptage of the token
ALGORITHM=HS256
```

---

## 📦 Dependencies

- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL adapter
- `passlib[bcrypt]` - Password hashing
- `python-jose[cryptography]` - JWT token handling
- `pydantic` - Data validation
- `python-dotenv` - Environment variable management

---

## 🚀 Deployment

Configure your hosting environment with the required environment variables and run:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📝 License

EIP Project - Epitech 2027

---

## 👥 Support

For issues or questions, contact the development team.