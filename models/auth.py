from pydantic import BaseModel, EmailStr

class SignUpSchema(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str

class SignInSchema(BaseModel):
    username: str
    password: str
