import os
import uuid
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from transformers import AutoModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import ApiException

EMBEDDING_MODEL = "jinaai/jina-clip-v1"
COLLECTION_NAME = "reddit"
VECTOR_SIZE = 768
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

QDRANT_CREDENTIALS = {"url": os.getenv("QDRANT_URL")}

if QDRANT_API_KEY:
    QDRANT_CREDENTIALS["api_key"] = QDRANT_API_KEY


def initialize_model():
    return AutoModel.from_pretrained(EMBEDDING_MODEL, trust_remote_code=True)


def setup_qdrant_client():
    client = QdrantClient(**QDRANT_CREDENTIALS)
    if not client.collection_exists(COLLECTION_NAME):
        try:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.DOT),
            )
        except ApiException as e:
            print(f"Error creating collection: {e}")
    return client


def validate_and_load_image(image_url):
    """
    Validate and load an image from a URL, with proper error handling.
    Returns None if the image is invalid or cannot be loaded.
    """
    try:
        # Add timeout to prevent hanging on slow responses
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Try to open the image to validate it
        image = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary (handles PNG with transparency)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            image = image.convert('RGB')
            
        return image
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from {image_url}: {e}")
        return None
    except UnidentifiedImageError:
        print(f"Could not identify image format for {image_url}")
        return None
    except Exception as e:
        print(f"Unexpected error processing image {image_url}: {e}")
        return None


def embed_and_store_post(client, model, post):
    embeddings = []

    # Always embed the title
    try:
        title_embedding = model.encode_text(post["title"])
        embeddings.append(
            PointStruct(id=str(uuid.uuid4()), vector=title_embedding, payload=post)
        )
    except Exception as e:
        print(f"Error embedding title: {e}")
        return None

    # Embed selftext if it exists and isn't empty
    if post.get("selftext", "").strip():
        try:
            selftext_embedding = model.encode_text(post["selftext"])
            embeddings.append(
                PointStruct(id=str(uuid.uuid4()), vector=selftext_embedding, payload=post)
            )
        except Exception as e:
            print(f"Error embedding selftext: {e}")

    # Handle image if it exists
    if "image_url" in post:
        image = validate_and_load_image(post["image_url"])
        if image:
            try:
                image_embedding = model.encode_image(image)
                embeddings.append(
                    PointStruct(id=str(uuid.uuid4()), vector=image_embedding, payload=post)
                )
            except Exception as e:
                print(f"Error embedding image: {e}")

    # Only proceed with storage if we have at least one valid embedding
    if embeddings:
        try:
            operation_info = client.upsert(
                collection_name=COLLECTION_NAME,
                wait=True,
                points=embeddings,
            )
            print(f"Post embedded and stored: {operation_info}")
            return operation_info
        except ApiException as e:
            print(f"Error storing post: {e}")
            return None
    else:
        print("No valid embeddings generated for post")
        return None


def search_posts(client, model, query, limit=3):
    try:
        search_query = model.encode_text(query)
        search_results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=search_query,
            with_payload=True,
            limit=limit,
        ).points
        return search_results
    except ApiException as e:
        print(f"Error searching posts: {e}")
        return []
    except Exception as e:
        print(f"Error encoding search query: {e}")
        return []