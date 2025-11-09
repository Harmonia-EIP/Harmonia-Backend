from fastapi import HTTPException

class UserAlreadyExistsException(HTTPException):
    def __init__(self, detail: str = "Username already exists"):
        super().__init__(status_code=400, detail=detail)

class InvalidCredentialsException(HTTPException):
    def __init__(self, detail: str = "Invalid username or password"):
        super().__init__(status_code=401, detail=detail)

class UserNotFoundException(HTTPException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=404, detail=detail)

class MissingParamException(HTTPException):
    def __init__(self, field_name: str):
        message = f"Le champ {field_name} est obligatoire."
        super().__init__(status_code=400, detail=message)