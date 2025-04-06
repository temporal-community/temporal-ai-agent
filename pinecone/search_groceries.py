import os
import yaml
import argparse
import logging
import time
from dotenv import load_dotenv
from openai import OpenAI
from pinecone.grpc import PineconeGRPC as Pinecone, GRPCClientConfig
from pinecone import Index, QueryResponse
from typing import Optional

# --- Configuration --- (Match preload script)
# Assuming script is run from workspace root
DOCKER_COMPOSE_PATH = "pinecone/docker-compose.yaml"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 768
TOP_K = 5 # Number of results to return
INDEX_NAME = "store-items" # Define the single index name

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Functions (Adapted from preload_vector_data.py) ---

def load_single_service_config(file_path: str, service_name: str) -> dict:
    """Loads the configuration for a specific service from docker-compose."""
    logging.info(f"Loading configuration for service '{service_name}' from {file_path}...")
    abs_file_path = os.path.abspath(file_path)
    if not os.path.exists(abs_file_path):
        # Try relative path from script location if running from pinecone/
        script_dir = os.path.dirname(__file__)
        rel_path = os.path.join(script_dir, '..', file_path)
        abs_file_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_file_path):
            logging.error(f"Error: Docker compose file not found at {abs_file_path} or relative path. Exiting.")
            exit(1)
        else:
            logging.info(f"Found config at relative path: {abs_file_path}")
    try:
        with open(abs_file_path, 'r') as f:
            config = yaml.safe_load(f)
        if not config or 'services' not in config or service_name not in config['services']:
            raise ValueError(f"Invalid docker-compose file or service '{service_name}' not found.")
        logging.info(f"Configuration for '{service_name}' loaded successfully.")
        return config['services'][service_name]
    except Exception as e:
        logging.error(f"Error loading/parsing YAML file {abs_file_path} for service '{service_name}': {e}")
        exit(1)

def generate_single_embedding(client: OpenAI, text: str) -> list[float]:
    """Generates an embedding for a single text string."""
    logging.debug(f"Generating embedding for query: '{text[:50]}...'")
    try:
        res = client.embeddings.create(
            input=[text],
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSION
        )
        logging.debug("Embedding generated successfully.")
        return res.data[0].embedding
    except Exception as e:
        logging.error(f"Error generating embedding for query '{text}': {e}")
        raise # Re-raise to stop the script if embedding fails

def search_index(index: Index, query_embedding: list[float], top_k: int, filter_dict: Optional[dict] = None):
    """Performs a query against the Pinecone index, optionally filtering by metadata."""
    logging.info(f"Querying index '{INDEX_NAME}' with top_k={top_k} and filter={filter_dict}...")
    try:
        query_response: QueryResponse = index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True,
            include_values=False
        )
        return query_response.matches
    except Exception as e:
        logging.error(f"Error querying index '{INDEX_NAME}': {e}")
        return []

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Search for grocery items in the single Pinecone index.")
    parser.add_argument("query", type=str, help="The grocery item or query to search for.")
    parser.add_argument("--store", type=str, help="Optional: Filter results by store name (e.g., Safeway, Trader Joe\'s, Whole Foods)")
    parser.add_argument("--top_k", type=int, default=TOP_K, help=f"Number of results to return (default: {TOP_K})")

    args = parser.parse_args()

    logging.info(f"Starting grocery search for query: '{args.query}'")
    if args.store:
        logging.info(f"Filtering by store: {args.store}")
    start_time = time.time()

    # Determine base path (workspace root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    logging.info(f"Workspace root detected as: {workspace_root}")
    docker_compose_full_path = os.path.join(workspace_root, DOCKER_COMPOSE_PATH)

    # 1. Load Environment Variables
    dotenv_path = os.path.join(workspace_root, '.env')
    load_dotenv(dotenv_path=dotenv_path, override=True)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logging.error(f"Error: OPENAI_API_KEY not found in environment variables or {dotenv_path}. Exiting.")
        exit(1)

    # 2. Initialize OpenAI Client
    logging.info("Initializing OpenAI client...")
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        # Optional: Test connection
        openai_client.models.list()
        logging.info("OpenAI client initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        exit(1)

    # 3. Generate Query Embedding
    try:
        query_embedding = generate_single_embedding(openai_client, args.query)
    except Exception:
        logging.error("Failed to generate query embedding. Exiting.")
        exit(1)

    # 4. Load Docker Compose Config for the single service
    service_config = load_single_service_config(docker_compose_full_path, INDEX_NAME)

    # Extract port
    port = None
    if 'ports' in service_config and service_config['ports']:
        port_mapping = service_config['ports'][0]
        try:
            port = int(port_mapping.split(':')[0])
            logging.info(f"Connecting to Pinecone service '{INDEX_NAME}' via port {port}")
        except (ValueError, IndexError, TypeError):
            logging.error(f"Could not parse host port for {INDEX_NAME}. Exiting.")
            exit(1)
    else:
        logging.error(f"No port mapping found for service {INDEX_NAME}. Exiting.")
        exit(1)

    # 5. Connect to the single Pinecone Instance
    pinecone_grpc_host = f"localhost:{port}"
    pc = None
    index = None
    try:
        logging.info(f"Connecting to index '{INDEX_NAME}' via gRPC (plaintext) at {pinecone_grpc_host}...")
        pc = Pinecone(api_key="dummy-key", host=pinecone_grpc_host, plaintext=True)
        index = pc.Index(
            name=INDEX_NAME,
            host=pinecone_grpc_host,
            grpc_config=GRPCClientConfig(secure=False)
        )
        logging.info(f"Successfully obtained index handle for '{INDEX_NAME}'.")

        # 6. Prepare Filter
        query_filter = None
        if args.store:
            # Basic validation for known stores, could be expanded
            known_stores = ["Safeway", "Trader Joe's", "Whole Foods"]
            if args.store not in known_stores:
                 logging.warning(f"Store '{args.store}' not in known list {known_stores}. Filter might yield no results if store name is incorrect.")
            query_filter = {"store": args.store}

        # 7. Perform Search
        search_results = search_index(index, query_embedding, args.top_k, query_filter)

        # 8. Print Results
        print(f"\n--- Search Results for '{args.query}' (Top {args.top_k}{f' in {args.store}' if args.store else ' across all stores'}) ---")
        if search_results:
            for match in search_results:
                score = match.get('score', 0)
                metadata = match.metadata
                store = metadata.get('store', 'N/A')
                category = metadata.get('category', 'N/A')
                chunk_text = metadata.get('original_chunk', '[Chunk text not found in metadata]')
                print(f"\n[Score: {score:.4f}] [Store: {store}] [Category: {category}]")
                print(f"Chunk: {chunk_text}")
        else:
            print("No results found matching the query and filter criteria.")

    except Exception as e:
        logging.error(f"An error occurred during connection or search: {e}")
    finally:
        # Clean up client connection
        if pc:
            del pc
            logging.debug(f"Pinecone client object for {INDEX_NAME} deleted.")

    end_time = time.time()
    logging.info(f"\nSearch script finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main() 