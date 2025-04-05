import os
import yaml
import argparse
import logging
import time
from dotenv import load_dotenv
from openai import OpenAI
from pinecone.grpc import PineconeGRPC as Pinecone, GRPCClientConfig
from pinecone import Index

# --- Configuration --- (Match preload script)
# Assuming script is run from workspace root
DOCKER_COMPOSE_PATH = "pinecone/docker-compose.yaml"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 768
TOP_K = 5 # Number of results to return per store

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Functions (Adapted from preload_vector_data.py) ---

def load_config(file_path: str) -> dict:
    """Loads the docker-compose configuration."""
    logging.info(f"Loading configuration from {file_path}...")
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
        if not config or 'services' not in config:
            raise ValueError("Invalid docker-compose file: 'services' key not found.")
        logging.info("Configuration loaded successfully.")
        return config['services']
    except Exception as e:
        logging.error(f"Error loading/parsing YAML file {abs_file_path}: {e}")
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

def search_store(index: Index, query_embedding: list[float], top_k: int):
    """Performs a query against a specific Pinecone index."""
    try:
        query_response = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            include_values=False # Usually don't need the vectors themselves in results
        )
        return query_response.matches
    except Exception as e:
        logging.error(f"Error querying index '{index.name}': {e}")
        return []

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Search for grocery items across local Pinecone stores.")
    parser.add_argument("query", type=str, help="The grocery item or query to search for.")
    args = parser.parse_args()

    logging.info(f"Starting grocery search for query: '{args.query}'")
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

    # 4. Load Docker Compose Config
    services = load_config(docker_compose_full_path)

    # 5. Iterate through stores, connect, and search
    all_results = {}
    for service_name, service_config in services.items():
        logging.info(f"\n--- Searching store: {service_name} ---")

        # Extract port
        port = None
        if 'ports' in service_config and service_config['ports']:
            port_mapping = service_config['ports'][0]
            try:
                port = int(port_mapping.split(':')[0])
                logging.info(f"Found host port mapping: {port}")
            except (ValueError, IndexError, TypeError):
                logging.warning(f"Could not parse host port for {service_name}. Skipping store.")
                continue
        else:
            logging.warning(f"No port mapping found for service {service_name}. Skipping store.")
            continue

        # Connect to Pinecone Instance (using gRPC plaintext + GRPCClientConfig)
        pinecone_grpc_host = f"localhost:{port}"
        index_name = service_name
        pc = None
        index = None
        try:
            logging.info(f"Connecting to index '{index_name}' via gRPC (plaintext) at {pinecone_grpc_host}...")
            # Initialize client (host here might be less critical if index host is specified below)
            pc = Pinecone(api_key="dummy-key", host=pinecone_grpc_host, plaintext=True)

            # Get index handle with explicit insecure config for data plane
            index = pc.Index(
                name=index_name,
                host=pinecone_grpc_host,
                grpc_config=GRPCClientConfig(secure=False)
            )
            logging.info(f"Successfully obtained index handle for '{index_name}'.")

            # Perform search
            logging.info(f"Querying index '{index_name}'...")
            store_results = search_store(index, query_embedding, TOP_K)
            all_results[service_name] = store_results

            # Print results for this store
            if store_results:
                print(f"\nResults from {service_name}:")
                for match in store_results:
                    score = match.get('score', 0)
                    name = match.metadata.get('name', 'N/A')
                    price = match.metadata.get('price', 'N/A')
                    print(f"  - Score: {score:.4f} | Name: {name} | Price: {price}")
            else:
                print(f"\nNo results found in {service_name}.")

        except Exception as e:
            logging.error(f"Failed to connect or search index '{index_name}': {e}")
        finally:
            # Clean up client connection for the store
            if pc:
                # No explicit close needed for Pinecone client object, rely on GC
                del pc
                logging.debug(f"Pinecone client object for {service_name} deleted.")

    end_time = time.time()
    logging.info(f"\nSearch script finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main() 