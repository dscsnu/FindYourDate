from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    gender = Column(String, nullable=False)  # male, female, non-binary
    orientation = Column(String, nullable=False)  # straight, gay, bi, etc.
    accept_non_straight = Column(Boolean, default=True)
    preferences = Column(JSON, default=list)  # ex. ["male", "female"]
    embedding_id = Column(Integer, ForeignKey("embeddings.id"), nullable=True)
    accept_non_straight = Column(Boolean, default=True)  # whether user is open to bi or non-straight matches

    embedding = relationship("Embedding", back_populates="user")
    matches = relationship("MatchHistory", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} name={self.name}>"