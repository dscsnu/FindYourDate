from sqlalchemy import Column, Integer, ForeignKey, Float, String, Enum
from sqlalchemy.orm import relationship
from .base import Base
import enum

class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class MatchHistory(Base):
    __tablename__ = "match_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    matched_user_id = Column(Integer)
    similarity_score = Column(Float)
    algorithm_used = Column(String, default="cosine")
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING)

    user = relationship("User", back_populates="matches")

    def __repr__(self):
        return f"<MatchHistory user={self.user_id} matched={self.matched_user_id} score={self.similarity_score}>"