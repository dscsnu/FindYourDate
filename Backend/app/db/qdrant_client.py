from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

qdrant = QdrantClient(host="localhost", port=6333)

# vectors is a 1D nparray
def store_embedding(vector, user_id):
    qdrant.upsert(
        collection_name="find_my_date",
        points=[PointStruct(id=user_id, vector=vector.tolist())],
    )