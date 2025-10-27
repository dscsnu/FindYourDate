"""
Test script to verify embeddings are working correctly.
This will:
1. Retrieve a stored vector from Qdrant
2. Create embeddings for test sentences
3. Calculate cosine similarity
4. Show which sentences are most similar

This helps verify that the embedding system is working correctly.
"""

import os
import uuid
import numpy as np
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Get configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "find_my_date")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def email_to_uuid(email: str) -> str:
    """Convert email to UUID"""
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
    return str(uuid.uuid5(namespace, email))

def get_text_embedding(text: str):
    """Convert text to embedding using OpenAI"""
    if not text:
        return []
    res = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return res.data[0].embedding

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def test_embeddings(email: str, test_sentences: list):
    """Test embeddings by comparing test sentences with stored vector"""
    
    print("=" * 80)
    print("EMBEDDING SIMILARITY TEST")
    print("=" * 80)
    print(f"\n🔍 Testing against stored vector for: {email}\n")
    
    # Retrieve stored vector
    point_id = email_to_uuid(email)
    try:
        result = qdrant.retrieve(
            collection_name=QDRANT_COLLECTION,
            ids=[point_id],
            with_vectors=True
        )
        
        if not result or len(result) == 0:
            print(f"❌ No vector found for email: {email}")
            return
        
        stored_vector = result[0].vector
        print(f"✅ Retrieved stored vector ({len(stored_vector)} dimensions)\n")
        
    except Exception as e:
        print(f"❌ Error retrieving vector: {e}")
        return
    
    # Test each sentence
    print("=" * 80)
    print("TESTING SENTENCES")
    print("=" * 80)
    
    similarities = []
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n📝 Test #{i}:")
        print(f"   Sentence: \"{sentence}\"")
        
        # Create embedding for test sentence
        test_embedding = get_text_embedding(sentence)
        
        if not test_embedding:
            print(f"   ❌ Failed to create embedding")
            continue
        
        # Calculate similarity
        similarity = cosine_similarity(stored_vector, test_embedding)
        similarities.append((sentence, similarity))
        
        # Interpret similarity score
        if similarity > 0.9:
            interpretation = "🟢 EXTREMELY SIMILAR"
        elif similarity > 0.8:
            interpretation = "🟢 VERY SIMILAR"
        elif similarity > 0.7:
            interpretation = "🟡 MODERATELY SIMILAR"
        elif similarity > 0.6:
            interpretation = "🟡 SOMEWHAT SIMILAR"
        else:
            interpretation = "🔴 NOT VERY SIMILAR"
        
        print(f"   Similarity: {similarity:.4f} - {interpretation}")
    
    # Show ranking
    print("\n" + "=" * 80)
    print("RANKING (Most to Least Similar)")
    print("=" * 80)
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (sentence, similarity) in enumerate(similarities, 1):
        print(f"\n{rank}. Similarity: {similarity:.4f}")
        print(f"   \"{sentence[:80]}{'...' if len(sentence) > 80 else ''}\"")
    
    # Show interpretation
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print("""
📊 Similarity Score Guide:
   • 0.90-1.00: Extremely similar (almost identical meaning)
   • 0.80-0.90: Very similar (strong semantic overlap)
   • 0.70-0.80: Moderately similar (related topics)
   • 0.60-0.70: Somewhat similar (some connection)
   • Below 0.60: Not very similar (different topics)

✅ If embeddings are working correctly:
   - Similar sentences should have scores > 0.7
   - Dissimilar sentences should have scores < 0.6
   - The ranking should make intuitive sense
    """)

def search_similar_users(email: str, top_k: int = 5):
    """Search for most similar users using Qdrant's built-in search"""
    
    print("\n" + "=" * 80)
    print("FINDING SIMILAR USERS")
    print("=" * 80)
    print(f"\n🔍 Finding users most similar to: {email}\n")
    
    # Get the vector for this email
    point_id = email_to_uuid(email)
    try:
        result = qdrant.retrieve(
            collection_name=QDRANT_COLLECTION,
            ids=[point_id],
            with_vectors=True
        )
        
        if not result or len(result) == 0:
            print(f"❌ No vector found for email: {email}")
            return
        
        query_vector = result[0].vector
        
        # Search for similar vectors
        search_results = qdrant.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=top_k + 1,  # +1 because the user itself will be in results
            with_payload=True
        )
        
        print(f"✅ Found {len(search_results)} results:\n")
        
        for i, hit in enumerate(search_results, 1):
            user_email = hit.payload.get('email', 'Unknown')
            similarity = hit.score
            
            if user_email == email:
                print(f"{i}. {user_email} (THIS USER)")
            else:
                interpretation = ""
                if similarity > 0.8:
                    interpretation = "🟢 Very Compatible"
                elif similarity > 0.7:
                    interpretation = "🟡 Compatible"
                else:
                    interpretation = "🔴 Less Compatible"
                
                print(f"{i}. {user_email}")
                print(f"   Similarity: {similarity:.4f} - {interpretation}")
        
    except Exception as e:
        print(f"❌ Error searching: {e}")

if __name__ == "__main__":
    # Email to test against
    test_email = "rj142@snu.edu.in"
    
    # Test sentences - mix of similar and different topics
    test_sentences = [
        # These should be similar if the user is outgoing/social
        "I love going out with friends and meeting new people at parties",
        "I'm very social and enjoy being around people",
        "I prefer quiet nights at home reading books",
        
        # These test interests/hobbies
        "I enjoy outdoor activities like hiking and camping",
        "I love video games and watching movies at home",
        "I'm passionate about art and creative projects",
        
        # These test personality traits
        "I value honesty and open communication in relationships",
        "I'm looking for someone adventurous and spontaneous",
        "I prefer someone calm and peaceful",
        
        # Random different topic
        "The weather today is quite nice and sunny",
    ]
    
    print("\n🧪 TESTING EMBEDDINGS FUNCTIONALITY\n")
    
    # Test 1: Compare with test sentences
    test_embeddings(test_email, test_sentences)
    
    # Test 2: Find similar users in database
    search_similar_users(test_email, top_k=5)
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
