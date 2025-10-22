from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import os

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")  # full postgres:// URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

qdrant = QdrantClient(host="localhost", port=6333)


# vectors is a 1D nparray
def store_embedding(vector, user_id):
    qdrant.upsert(
        collection_name="find_my_date",
        points=[PointStruct(id=user_id, vector=vector.tolist())],
    )
