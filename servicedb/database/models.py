from sqlalchemy import Column, Integer, Text, String
from .db import Base


class Posts(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    surname = Column(String(255))
    patronymic = Column(String(255))
    phone = Column(String(255))
    text = Column(Text)

