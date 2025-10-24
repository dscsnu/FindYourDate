from numpy.linalg import norm
import numpy as np

def cosine_similarity(vec1, vec2):
    if norm(vec1) == 0 or norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def valid_partner(a, b):
    if a.id == b.id:
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