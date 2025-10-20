from sqlalchemy import Column, Integer, JSON, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    vector = Column(JSON, nullable=False)
    model_name = Column(String, default="text-embedding-3-large")
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="embedding")

    def __repr__(self):
        return f"<Embedding id={self.id} user_id={self.user_id}>"