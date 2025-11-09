from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from database.connection import get_db
from services.profile_service import ProfileService
from schemas.profile import ProfileSchema

router = APIRouter()

@router.get("/me", response_model=ProfileSchema)
def get_my_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    service = ProfileService(db)

    current_user = service.get_current_user(authorization)

    return service.get_profile(current_user)
