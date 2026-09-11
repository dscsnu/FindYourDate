from app.core.llm import client, llm_slot


def get_text_embedding(text: str):
    if not text:
        return []
    with llm_slot():
        res = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
    return res.data[0].embedding
