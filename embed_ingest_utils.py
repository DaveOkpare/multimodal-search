import uuid
from transformers import AutoModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import ApiException

EMBEDDING_MODEL = "jinaai/jina-clip-v1"
COLLECTION_NAME = "reddit"
VECTOR_SIZE = 768


def initialize_model():
    return AutoModel.from_pretrained(EMBEDDING_MODEL, trust_remote_code=True)


def setup_qdrant_client():
    client = QdrantClient(url="http://localhost:6333")
    if not client.collection_exists(COLLECTION_NAME):
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.DOT),
            )
        except ApiException as e:
            print(f"Error creating collection: {e.content}")
    return client


def embed_and_store_post(client, model, post):
    embeddings = []

    title_embedding = model.encode_text(post["title"])
    embeddings.append(
        PointStruct(id=str(uuid.uuid4()), vector=title_embedding, payload=post)
    )

    if post["selftext"].strip() != "":
        selftext_embedding = model.encode_text(post["selftext"])
        embeddings.append(
            PointStruct(id=str(uuid.uuid4()), vector=selftext_embedding, payload=post)
        )

    if "image_url" in post:
        image_embedding = model.encode_image(post["image_url"])
        embeddings.append(
            PointStruct(id=str(uuid.uuid4()), vector=image_embedding, payload=post)
        )

    try:
        operation_info = client.upsert(
            collection_name=COLLECTION_NAME,
            wait=True,
            points=embeddings,
        )
        print(f"Post embedded and stored: {operation_info}")
        return operation_info
    except ApiException as e:
        print(f"Error storing post: {e.content}")
        return None


def search_posts(client, model, query, limit=3):
    search_query = model.encode_text(query)

    try:
        search_results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=search_query,
            with_payload=True,
            limit=limit,
        ).points
        return search_results
    except ApiException as e:
        print(f"Error searching posts: {e.content}")
        return []
