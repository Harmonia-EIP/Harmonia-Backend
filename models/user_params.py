from database.base import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class UserParams(Base):
    __tablename__ = "user_params"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme_id = Column(Integer, nullable=False, default=0)   # 0 = Dark, 1 = Light, etc.
    layout_id = Column(Integer, nullable=False, default=0)  # 0 = Layout1, 1 = Layout2, etc.

    user = relationship("User", back_populates="params")
