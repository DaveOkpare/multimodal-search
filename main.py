from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import os
from dotenv import load_dotenv
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

# DAG default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def fetch_and_process_reddit_data(**context):
    # Load environment variables
    load_dotenv()
    
    # Initialize Reddit credentials
    creds = Credential(
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        secret_key=os.getenv("REDDIT_SECRET_KEY"),
    )
    
    # Set up headers and get access token
    headers = {"User-Agent": "MultimodalSearch/0.0.1"}
    token = get_access_token(creds, headers)
    headers.update({"Authorization": f"bearer {token}"})
    
    # Fetch Reddit data
    data = fetch_data(subreddit="pics", filter_by="hot", headers=headers)
    
    # Initialize model and database client
    model = initialize_model()
    client = setup_qdrant_client()
    
    # Process and store posts
    processed_posts = [
        embed_and_store_post(client, model, post)
        for post in extract_reddit_post_info(data)
    ]
    
    return f"Processed {len(processed_posts)} posts"

# Create the DAG
with DAG(
    'reddit_data_ingestion',
    default_args=default_args,
    description='Reddit data fetching and ingestion to vector database every 2 minutes',
    schedule_interval='*/2 * * * *',  # Run every 2 minutes using cron syntax
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['reddit', 'vector_db'],
) as dag:
    
    # Task to fetch and process Reddit data
    fetch_and_ingest = PythonOperator(
        task_id='fetch_and_ingest_reddit_data',
        python_callable=fetch_and_process_reddit_data,
        provide_context=True,
    )

    # Add task dependencies if you add more tasks
    fetch_and_ingest