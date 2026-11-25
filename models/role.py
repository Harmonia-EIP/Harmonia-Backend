from sqlalchemy import Column, Integer, String

from database.base import Base

# Ids fixes, créés par seed_initial_data.py
ROLE_ADMIN_ID = 1
ROLE_STAFF_ID = 2
ROLE_USER_ID = 3

ROLE_CODE_BY_ID = {ROLE_ADMIN_ID: "ADMIN", ROLE_STAFF_ID: "STAFF", ROLE_USER_ID: "USER"}
ROLE_ID_BY_CODE = {code: role_id for role_id, code in ROLE_CODE_BY_ID.items()}


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False, index=True)
    label = Column(String, nullable=False)
    description = Column(String)
