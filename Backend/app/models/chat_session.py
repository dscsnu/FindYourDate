from sqlalchemy import Column, Integer, ForeignKey, JSON, String, DateTime, func
from sqlalchemy.orm import relationship
from db.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    phase = Column(String, default="personality")  # personality / social
    step = Column(Integer, default=0)              # which question number
    history = Column(JSON, default=list)           # [{q: "...", a: "..."}]
    last_question = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="chat_session")