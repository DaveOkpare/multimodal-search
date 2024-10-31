import os
from dotenv import load_dotenv
import modal

from embed_ingest_utils import (
    embed_and_store_post,
    initialize_model,
    setup_qdrant_client,
)
from fetch_reddit_posts import (
    Credential,
    fetch_data,
    get_access_token,
    extract_reddit_post_info,
)

load_dotenv()

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install([
        "python-dotenv==1.0.1",
        "requests==2.32.3",
        "pydantic==2.9.2",
        "transformers==4.45.2",
        "timm==1.0.11",
        "einops==0.8.0",
        "qdrant_client==1.12.0",
        "pillow==10.4.0",
    ])
)

app = modal.App(image=image)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET_KEY = os.getenv("REDDIT_SECRET_KEY")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")


creds = Credential(
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    client_id=REDDIT_CLIENT_ID,
    secret_key=REDDIT_SECRET_KEY,
)

headers = {"User-Agent": "MultimodalSearch/0.0.1"}

token = get_access_token(creds, headers)

headers = {**headers, **{"Authorization": f"bearer {token}"}}

data = fetch_data(subreddit="pics", filter_by="hot", headers=headers)


@app.function(schedule=modal.Period(days=1), secrets=[modal.Secret.from_name("multimodal-search")])
def process_and_store_reddit_posts():
    model = initialize_model()
    client = setup_qdrant_client()

    [
        embed_and_store_post(client, model, post)
        for post in extract_reddit_post_info(data)
    ]


if __name__ == "__main__":
    process_and_store_reddit_posts()
