# Reddit Multimodal Search

A multimodal search system that enables semantic search across Reddit posts using both text and image content. The system ingests posts from specified subreddits, generates embeddings for text and images using CLIP, and stores them in a Qdrant vector database for efficient similarity search.

## Features

- Automated daily ingestion of Reddit posts
- Text and image embedding using CLIP model
- Vector similarity search via Qdrant
- Streamlit web interface for searching posts
- Support for both image and text-based posts
- Configurable search results with adjustable result limits

## System Architecture

The system consists of four main components:

1. **Data Collection** (`fetch_reddit_posts.py`)
   - Handles Reddit API authentication
   - Fetches posts from specified subreddits
   - Extracts relevant post information

2. **Embedding Generation** (`embed_ingest_utils.py`)
   - Generates embeddings for post titles, text, and images
   - Handles image downloading and preprocessing
   - Manages vector storage in Qdrant

3. **Search Service** (`embed_ingest_utils.py`)
   - Provides vector similarity search functionality
   - Converts search queries into embeddings
   - Returns relevant posts based on similarity

4. **Web Interface** (`streamlit_app.py`)
   - Provides user interface for searching
   - Displays search results with images and links
   - Configurable number of results

## Setup

### Prerequisites

- Python 3.12
- Reddit API credentials
- Qdrant instance (cloud or local)

### Environment Variables

Create a `.env` file with the following variables:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_SECRET_KEY=your_secret_key
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key # optional in local instance
```

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- python-dotenv==1.0.1
- requests==2.32.3
- pydantic==2.9.2
- transformers==4.45.2
- timm==1.0.11
- einops==0.8.0
- qdrant_client==1.12.0
- pillow==10.4.0
- streamlit

### Deployment

The system uses Modal for serverless deployment:

1. Deploy the ingestion function:
```bash
modal deploy main.py
```

2. Run the Streamlit interface:
```bash
streamlit run streamlit_app.py
```

## Usage

### Data Ingestion

The system automatically ingests Reddit posts daily using Modal's scheduling:

```python
@app.function(schedule=modal.Period(days=1), secrets=[modal.Secret.from_name("multimodal-search")])
def process_and_store_reddit_posts():
    # Ingestion logic
```

### Searching

1. Access the Streamlit interface through your browser
2. Enter your search query in the text input
3. Adjust the number of results using the slider
4. Click "Search" to see matching posts

## Vector Store Configuration

The system uses Qdrant with the following configuration:

- Collection Name: "reddit"
- Vector Size: 768 (CLIP embedding dimension)
- Distance Metric: DOT product
- Embedding Model: "jinaai/jina-clip-v1"

## Error Handling

The system includes comprehensive error handling for:
- Image downloads and processing
- API rate limits and timeouts
- Embedding generation
- Vector storage operations
- Invalid or corrupt images
- Gallery posts (currently skipped)

## Limitations

- Gallery posts are not currently supported
- Reddit API rate limits may affect ingestion speed
- Memory usage scales with batch size during ingestion

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a detailed description of changes

## License

MIT License

Copyright (c) 2024 David Okpare
