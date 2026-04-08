from database.base import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship


class UserParams(Base):
    __tablename__ = "user_params"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme_id = Column(Integer, nullable=False, default=0)
    layout_id = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="params")

    @property
    def get_theme_id(self):
        return self.theme_id

    @get_theme_id.setter
    def set_theme_id(self, value: int):
        self.theme_id = value

    @property
    def get_layout_id(self):
        return self.layout_id

    @get_layout_id.setter
    def set_layout_id(self, value: int):
        self.layout_id = value