from sqlalchemy import Column, Integer, Float, ForeignKey, String
from .base import Base

class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(Integer, primary_key=True)
    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    similarity_score = Column(Float, nullable=False)
    algorithm_used = Column(String, default="cosine")
    batch_id = Column(String, nullable=True)

    def __repr__(self):
        return f"<MatchScore {self.user_a_id}-{self.user_b_id} score={self.similarity_score:.3f}>"