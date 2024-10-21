from typing import Literal
import requests
from pydantic import BaseModel


class Credential(BaseModel):
    username: str
    password: str
    client_id: str
    secret_key: str


def get_access_token(credentials: Credential, headers: dict) -> str:
    auth = requests.auth.HTTPBasicAuth(credentials.client_id, credentials.secret_key)

    data = {
        "grant_type": "password",
        "username": credentials.username,
        "password": credentials.password,
    }

    # send our request for an OAuth token
    res = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=auth,
        data=data,
        headers=headers,
    )

    # convert response to JSON and pull access_token value
    return res.json()["access_token"]


def fetch_data(
    subreddit: str, filter_by: Literal["hot", "new", "top"], headers: dict
) -> list:
    res = requests.get(
        f"https://oauth.reddit.com/r/{subreddit}/{filter_by}", headers=headers
    )
    return res.json()["data"]["children"]


def extract_reddit_post_info(posts: list):
    def build_output(data):
        if "is_gallery" in data:
            return None  # Skip gallery posts

        output = {
            "title": data["title"],
            "selftext": data["selftext"],
            "permalink": "https://reddit.com" + data["permalink"],
        }

        if "post_hint" in data:
            output["image_url"] = data["url"]
        else:
            output["url"] = data["url"]

        return output

    return [
        post
        for post in (build_output(post["data"]) for post in posts)
        if post is not None
    ]
