from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    gender = Column(String, nullable=False)
    orientation = Column(String, nullable=False)
    accept_non_straight = Column(Boolean, default=True)
    agePreference = Column(Integer, nullable=True) # 1 for higher or same, 0 for no preference, -1 for lower or same
    age = Column(Integer, nullable=False)

    matches = relationship("MatchHistory", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} name={self.name}>"
