from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from app import Base


class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())


class AdModel(Base):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
        }
