from sqlalchemy import Column, Integer, Text, String, ForeignKey
from .base import Base

class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=True)  # ex. "personality", "attachment" or whatever

    def __repr__(self):
        return f"<QuestionAnswer user={self.user_id} category={self.category}>"