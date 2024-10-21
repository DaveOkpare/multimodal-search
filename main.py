
import os
from dotenv import load_dotenv
from fetch_reddit_posts import Credential, fetch_data, get_access_token, extract_reddit_post_info

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET_KEY = os.getenv("REDDIT_SECRET_KEY")
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')


creds = Credential(username=REDDIT_USERNAME, password=REDDIT_PASSWORD, client_id=REDDIT_CLIENT_ID, secret_key=REDDIT_SECRET_KEY)

headers = {'User-Agent': 'MultimodalSearch/0.0.1'}

token = get_access_token(creds, headers)

headers = {**headers, **{'Authorization': f"bearer {token}"}}

data = fetch_data(subreddit="pics", filter_by="hot", headers=headers)

print(extract_reddit_post_info(data))
