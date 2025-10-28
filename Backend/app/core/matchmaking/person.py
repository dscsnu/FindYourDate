from app.models.user_model import User
from app.db.qdrant_client import get_embedding

class Person:
    def __init__(self, user: User):
        self.db_id = user.id
        self.name = user.name
        self.gender = user.gender[0].upper()  # 'M' or 'W'
        # Normalize orientation: "bisexual" -> "bi", keep others as-is
        self.orientation = "bi" if user.orientation.lower() == "bisexual" else user.orientation.lower()
        self.accepts_bi = user.accept_non_straight
        self.preferences = []
        self.similarity_scores = {}  # Maps Person -> similarity score
        self.matched_to = None
        self.age = user.age
        self.phone = user.phone
        self.email = user.email
        self.age_preference = user.age_preference
        # Fetch embedding from Qdrant vector database
        self.embedding = get_embedding(user.email)

    def __repr__(self):
        return f"{self.name}({self.gender},{self.orientation})"