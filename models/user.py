from database.base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    info = relationship("UserInfo", back_populates="user", uselist=False)
    params = relationship("UserParams", back_populates="user", uselist=False)

    @property
    def get_email(self):
        return self.email

    @get_email.setter
    def set_email(self, value: str):
        self.email = value

    @property
    def get_password_hash(self):
        return self.password_hash

    @get_password_hash.setter
    def set_password_hash(self, value: str):
        self.password_hash = value

    @property
    def get_is_active(self):
        return self.is_active

    @get_is_active.setter
    def set_is_active(self, value: bool):
        self.is_active = value

    @property
    def get_role_id(self):
        return self.role_id

    @get_role_id.setter
    def set_role_id(self, value: int):
        self.role_id = value