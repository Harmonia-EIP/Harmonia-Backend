from database.base import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class UserInfo(Base):
    __tablename__ = "user_info"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    avatar_url = Column(String)

    user = relationship("User", back_populates="info")

    @property
    def get_first_name(self):
        return self.first_name

    @get_first_name.setter
    def set_first_name(self, value: str):
        self.first_name = value

    @property
    def get_last_name(self):
        return self.last_name

    @get_last_name.setter
    def set_last_name(self, value: str):
        self.last_name = value

    @property
    def get_username(self):
        return self.username

    @get_username.setter
    def set_username(self, value: str):
        self.username = value

    @property
    def get_avatar_url(self):
        return self.avatar_url

    @get_avatar_url.setter
    def set_avatar_url(self, value: str):
        self.avatar_url = value