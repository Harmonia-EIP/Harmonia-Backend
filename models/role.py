from database.base import Base
from sqlalchemy import Column, Integer, String


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False, index=True)
    label = Column(String, nullable=False)
    description = Column(String)

    @property
    def get_code(self):
        return self.code

    @get_code.setter
    def set_code(self, value: str):
        self.code = value

    @property
    def get_label(self):
        return self.label

    @get_label.setter
    def set_label(self, value: str):
        self.label = value

    @property
    def get_description(self):
        return self.description

    @get_description.setter
    def set_description(self, value: str):
        self.description = value