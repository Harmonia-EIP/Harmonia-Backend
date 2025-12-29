from database.base import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False, index=True)
    label = Column(String, nullable=False)
    description = Column(String)

    users = relationship("User", secondary="user_roles", back_populates="roles")
