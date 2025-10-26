import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from dotenv import load_dotenv

load_dotenv()

# Get Qdrant configuration from environment variables
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "find_my_date")

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def email_to_uuid(email: str) -> str:
    """Convert email to a consistent UUID using namespace UUID"""
    # Use UUID5 (name-based, SHA-1) with a custom namespace
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    return str(uuid.uuid5(namespace, email))

# vectors is a 1D nparray
def store_embedding(vector, user_email):
    point_id = email_to_uuid(user_email)
    qdrant.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[PointStruct(
            id=point_id, 
            vector=vector.tolist(),
            payload={"email": user_email}  # Store email in payload for reference
        )],
    )

def get_embedding(user_email):
    point_id = email_to_uuid(user_email)
    try:
        result = qdrant.retrieve(
            collection_name=QDRANT_COLLECTION,
            ids=[point_id],
            with_vectors=True  # Important: retrieve the actual vectors!
        )
        if result and len(result) > 0:
            return result[0].vector
        return None
    except Exception as e:
        print(f"Error retrieving embedding: {e}")
        return None