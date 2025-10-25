from app.models.user import User

class Person:
    def __init__(self, user: User):
        self.db_id = user.id
        self.name = user.name
        self.gender = user.gender[0].upper()  # 'M' or 'W'
        self.orientation = user.orientation
        self.accepts_bi = user.accept_non_straight
        self.preferences = []
        self.similarity_scores = {}  # Maps Person -> similarity score
        self.matched_to = None

    def __repr__(self):
        return f"{self.name}({self.gender},{self.orientation})"