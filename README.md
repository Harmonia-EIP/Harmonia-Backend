# FastAPI Auth Backend (Single File Setup)

This project is a lightweight **FastAPI backend** for handling authentication (`/signup`, `/signin`) — ideal for connecting to a **JUCE frontend app** (C++ standalone GUI).  
It uses **bcrypt** password hashing, **JWT tokens**, and returns clean JSON responses with status and code fields.

---

## Requirements

- Python **3.10+**
- pip (Python package manager)

---

## Installation

Install dependencies:

```bash
pip install fastapi uvicorn passlib[bcrypt] python-jose[cryptography]
```

---

## Run the server

```bash
uvicorn main:app --reload
```


## Run on a custom port

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

---

## Project Structure

.
├── main.py                     
│
├── api/                       
│   └── auth.py                 
│
├── services/                   
│   └── auth_service.py         
│
├── utils/                      
│   └── jwt_handler.py          
│
├── models/                     
│   └── response_model.py       
│
└── README.md                   
