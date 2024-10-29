import os
import uuid
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from transformers import AutoModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import ApiException
import torch

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


def safe_download_image(url):
    """Safely download image content from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return None


def process_image_for_clip(image_url):
    """
    Process image specifically for CLIP model, handling various edge cases.
    Returns None if image cannot be processed.
    """
    try:
        # Download image content
        image_content = safe_download_image(image_url)
        if not image_content:
            return None

        # Try to open the image
        image = Image.open(BytesIO(image_content))

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Verify image isn't corrupt by accessing its size
        image.size

        return image

    except UnidentifiedImageError:
        print(f"Could not identify image format for {image_url}")
        return None
    except Exception as e:
        print(f"Error processing image {image_url}: {e}")
        return None


def safe_encode_image(model, image):
    """Safely encode image with CLIP model, handling potential errors."""
    try:
        with torch.no_grad():
            return model.encode_image(image)
    except Exception as e:
        print(f"Error encoding image with CLIP: {e}")
        return None


def embed_and_store_post(client, model, post):
    embeddings = []

    # Handle title embedding
    try:
        title_embedding = model.encode_text(post["title"])
        embeddings.append(
            PointStruct(id=str(uuid.uuid4()), vector=title_embedding, payload=post)
        )
    except Exception as e:
        print(f"Error embedding title: {e}")
        return None

    # Handle selftext embedding
    if post.get("selftext", "").strip():
        try:
            selftext_embedding = model.encode_text(post["selftext"])
            embeddings.append(
                PointStruct(id=str(uuid.uuid4()), vector=selftext_embedding, payload=post)
            )
        except Exception as e:
            print(f"Error embedding selftext: {e}")

    # Handle image embedding
    if "image_url" in post and post["image_url"]:
        processed_image = process_image_for_clip(post["image_url"])
        if processed_image:
            image_embedding = safe_encode_image(model, processed_image)
            if image_embedding is not None:
                embeddings.append(
                    PointStruct(id=str(uuid.uuid4()), vector=image_embedding, payload=post)
                )

    # Store embeddings if we have any
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
        with torch.no_grad():
            search_query = model.encode_text(query)
        search_results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=search_query,
            with_payload=True,
            limit=limit,
        ).points
        return search_results
    except Exception as e:
        print(f"Error in search_posts: {e}")
        return []