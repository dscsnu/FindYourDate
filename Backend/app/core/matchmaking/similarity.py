import numpy as np

def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors
    Returns a value between -1 and 1, where 1 means identical vectors
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

take_age_preference = True

def valid_partner(a, b):
    if a.email == b.email:
        return False

    if a.age < 18 or b.age < 18:
        if b.age < 18 and a.age < 18:
            pass
        else:
            return False

    if take_age_preference:
        if a.age_preference == -1 and b.age < a.age:
            return False
        if a.age_preference == 1 and b.age > a.age:
            return False
        if b.age_preference == -1 and a.age < b.age:
            return False
        if b.age_preference == 1 and a.age > b.age:
            return False

    if a.orientation == "straight":
        if a.gender == "M":
            if b.gender == "W":
                if b.orientation == "bi":
                    return a.accepts_bi
                elif b.orientation == "straight":
                    return True
                return False

        elif a.gender == "W":
            if b.gender == "M":
                if b.orientation == "bi":
                    return a.accepts_bi
                elif b.orientation == "straight":
                    return True
                return False

    if a.orientation == "gay":
        return a.gender == b.gender and b.orientation in ["gay", "bi"]

    if a.orientation == "lesbian":
        return a.gender == b.gender and b.orientation in ["lesbian", "bi"]

    if a.orientation == "bi":
        if b.orientation == "straight":
            if b.gender == "M" and a.gender == "W" and b.accepts_bi:
                return True
            if b.gender == "W" and a.gender == "M" and b.accepts_bi:
                return True
        if b.orientation == "gay" and b.gender == "M" and a.gender == "W":
            return False
        if b.orientation == "lesbian" and b.gender == "W" and a.gender == "M":
            return False
        return True

    return False
