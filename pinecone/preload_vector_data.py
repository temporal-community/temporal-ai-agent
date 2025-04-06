import os
import json
import yaml
import glob # Import glob to find files
from dotenv import load_dotenv
from openai import OpenAI
# Revert to gRPC client
from pinecone.grpc import PineconeGRPC as Pinecone, GRPCClientConfig # Import GRPCClientConfig
from pinecone import Index, UpsertResponse # Keep Index and UpsertResponse
from tqdm import tqdm
import time
import logging

# --- Configuration ---
# Adjusted paths assuming script is run from workspace root
# If running from `pinecone/` dir, change these
DOCKER_COMPOSE_PATH = "pinecone/docker-compose.yaml"
DATA_DIR = "pinecone/grocery_data"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 768  # Must match DIMENSION in docker-compose.yaml
BATCH_SIZE = 32 # Process items in batches for efficiency
INDEX_NAME = "store-items" # Define the single index name

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_config(file_path: str) -> dict:
    """Loads the docker-compose configuration."""
    logging.info(f"Loading configuration from {file_path}...")
    # Correct path relative to workspace root
    abs_file_path = os.path.abspath(file_path)
    if not os.path.exists(abs_file_path):
        logging.error(f"Error: Docker compose file not found at resolved path: {abs_file_path}")
        # Try relative path from script location if running from pinecone/
        script_dir = os.path.dirname(__file__)
        rel_path = os.path.join(script_dir, '..', file_path) # Go up one level
        abs_file_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_file_path):
             logging.error(f"Error: Also not found at relative path: {abs_file_path}")
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
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {abs_file_path}: {e}")
        exit(1)
    except ValueError as e:
        logging.error(f"Error in config file structure: {e}")
        exit(1)


def load_chunk_data(data_path: str) -> list[dict]:
    """Loads chunked grocery data from a JSON file.""" # Updated docstring
    logging.info(f"Loading chunk data from {data_path}...")
     # Correct path relative to workspace root
    abs_data_path = os.path.abspath(data_path)
    if not os.path.exists(abs_data_path):
        logging.warning(f"Data file not found at resolved path: {abs_data_path}. Trying relative...")
        # Try relative path from script location if running from pinecone/
        script_dir = os.path.dirname(__file__)
        rel_path = os.path.join(script_dir, '..', data_path) # Go up one level
        abs_data_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_data_path):
             logging.warning(f"Also not found at relative path: {abs_data_path}. Skipping file.")
             return []
        else:
             logging.info(f"Found data at relative path: {abs_data_path}")


    try:
        with open(abs_data_path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON data must be a list of chunks.")
        # Validate chunk structure
        valid_chunks = []
        for i, chunk in enumerate(data):
             if isinstance(chunk, dict) and 'store' in chunk and 'category' in chunk and 'chunk_text' in chunk:
                  valid_chunks.append(chunk)
             else:
                  logging.warning(f"Skipping invalid chunk structure at index {i} in {abs_data_path}: {chunk}")
        logging.info(f"Loaded {len(valid_chunks)} valid chunks from {abs_data_path}.")
        return valid_chunks
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {abs_data_path}. Skipping this file.")
        return []
    except ValueError as e:
        logging.error(f"Data file structure error ({abs_data_path}): {e}. Skipping this file.")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading data from {abs_data_path}: {e}")
        return []


# This function is not used with the standard Pinecone client initialization approach
# def get_pinecone_connection(host: str) -> Pinecone | None:
#     logging.warning("get_pinecone_connection function is deprecated, connection handled in main")
#     return None

def generate_embeddings(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a list of texts using OpenAI."""
    if not texts:
        return []
    logging.debug(f"Generating embeddings for {len(texts)} texts...")
    try:
        res = client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSION # Explicitly request dimension
        )
        logging.debug(f"Successfully generated {len(res.data)} embeddings.")
        return [record.embedding for record in res.data]
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        raise # Re-raise to stop the process if embedding fails critically

def upsert_batch(index: Index, batch: list[tuple[str, list[float], dict]]):
    """Upserts a batch of vectors to the Pinecone index."""
    if not batch:
        return
    logging.info(f"Upserting batch of {len(batch)} vectors...")
    try:
        upsert_response: UpsertResponse = index.upsert(vectors=batch)
        logging.info(f"Successfully upserted {upsert_response.upserted_count} vectors.")
        if upsert_response.upserted_count != len(batch):
             logging.warning(f"Mismatch in upsert count: Expected {len(batch)}, got {upsert_response.upserted_count}")
    except Exception as e:
        logging.error(f"Error upserting batch to Pinecone: {e}")
        # Consider adding retry logic here or logging failed batches for later processing

def main():
    """Main function to load data, generate embeddings, and upsert to Pinecone."""
    logging.info("Starting vector data preload script...")
    start_time = time.time()

    # Determine base path (workspace root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    logging.info(f"Workspace root detected as: {workspace_root}")
    docker_compose_full_path = os.path.join(workspace_root, DOCKER_COMPOSE_PATH)
    data_dir_full_path = os.path.join(workspace_root, DATA_DIR)


    # 1. Load Environment Variables (.env file from workspace root)
    dotenv_path = os.path.join(workspace_root, '.env')
    load_dotenv(dotenv_path=dotenv_path, override=True)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logging.error(f"Error: OPENAI_API_KEY not found in environment variables or {dotenv_path}.")
        exit(1)

    # 2. Initialize OpenAI Client
    logging.info("Initializing OpenAI client...")
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        openai_client.models.list() # Test connection
        logging.info("OpenAI client initialized and connection verified.")
    except Exception as e:
        logging.error(f"Failed to initialize or connect OpenAI client: {e}")
        exit(1)


    # 3. Load Docker Compose Config for the single service
    services = load_config(docker_compose_full_path)
    if INDEX_NAME not in services:
        logging.error(f"Error: Service '{INDEX_NAME}' not found in {docker_compose_full_path}.")
        exit(1)
    service_config = services[INDEX_NAME]
    logging.info(f"Found configuration for service '{INDEX_NAME}'.")

    # Extract port for the single service
    port = None
    if 'ports' in service_config and service_config['ports']:
        port_mapping = service_config['ports'][0]
        try:
            port = int(port_mapping.split(':')[0])
            logging.info(f"Using host port mapping for '{INDEX_NAME}': {port}")
        except (ValueError, IndexError, TypeError):
            logging.error(f"Could not parse host port from '{port_mapping}' for {INDEX_NAME}.")
            exit(1)
    else:
        logging.error(f"No port mapping found for service {INDEX_NAME} in {docker_compose_full_path}.")
        exit(1)

    # Dimension check
    try:
        config_dimension = int(service_config.get('environment', {}).get('DIMENSION'))
        if config_dimension != EMBEDDING_DIMENSION:
             logging.warning(f"Dimension mismatch for {INDEX_NAME}. Config: {config_dimension}, Script: {EMBEDDING_DIMENSION}. Using script dimension {EMBEDDING_DIMENSION}.")
    except (ValueError, TypeError):
         logging.warning(f"Could not read or parse DIMENSION from environment for {INDEX_NAME}. Assuming {EMBEDDING_DIMENSION}.")
    except Exception as e:
         logging.warning(f"Error reading dimension for {INDEX_NAME}: {e}. Assuming {EMBEDDING_DIMENSION}.")


    # 4. Load All Chunk Data from JSON files in the data directory
    all_chunks = []
    json_files = glob.glob(os.path.join(data_dir_full_path, "*.json"))
    if not json_files:
         logging.error(f"No JSON files found in {data_dir_full_path}. Nothing to process.")
         exit(1)

    logging.info(f"Found {len(json_files)} JSON files to process in {data_dir_full_path}.")
    for data_file in json_files:
        logging.info(f"--- Loading data from file: {os.path.basename(data_file)} ---")
        file_chunks = load_chunk_data(data_file)
        if file_chunks:
            all_chunks.extend(file_chunks)

    if not all_chunks:
        logging.error("No valid chunks loaded from any JSON file. Exiting.")
        exit(1)

    logging.info(f"Total valid chunks loaded from all files: {len(all_chunks)}")

    # 5. Connect to the Single Pinecone Instance using gRPC client with plaintext
    pinecone_grpc_host = f"localhost:{port}"
    logging.info(f"Attempting to connect to single Pinecone index '{INDEX_NAME}' via gRPC (plaintext) at {pinecone_grpc_host}...")

    pc = None
    index = None
    try:
        # Initialize Pinecone gRPC client with plaintext=True for local HTTP connection
        pc = Pinecone(api_key="dummy-key", host=pinecone_grpc_host, plaintext=True)

        # Directly attempt to get the index object handle, assuming it exists
        logging.info(f"Attempting to directly get gRPC index handle for '{INDEX_NAME}' at host {pinecone_grpc_host}...")
        index = pc.Index(
            name=INDEX_NAME,
            host=pinecone_grpc_host,
            grpc_config=GRPCClientConfig(secure=False) # Explicitly disable TLS for data operations
        )
        logging.info(f"Successfully obtained gRPC index handle for '{INDEX_NAME}'.")
        # Optional: Describe index stats
        try:
             stats = index.describe_index_stats()
             logging.info(f"Initial Index '{INDEX_NAME}' stats: {stats}")
        except Exception as desc_e:
             logging.warning(f"Could not describe_index_stats for {INDEX_NAME}: {desc_e}")

    except Exception as e:
        logging.error(f"Error connecting to or preparing index '{INDEX_NAME}' via gRPC at {pinecone_grpc_host}: {e}")
        if pc: del pc
        exit(1) # Exit if connection fails

    if not index:
        logging.error(f"Failed to get a valid gRPC index object for '{INDEX_NAME}'. Skipping upserts.")
        exit(1)

    # 6. Process and Upsert Chunk Data in Batches
    logging.info(f"Processing {len(all_chunks)} total chunks for upsertion into '{INDEX_NAME}'...")
    total_chunks_processed = 0
    try:
        for i in tqdm(range(0, len(all_chunks), BATCH_SIZE), desc=f"Upserting chunks to {INDEX_NAME}", unit="batch"):
            batch_chunks = all_chunks[i : i + BATCH_SIZE]
            if not batch_chunks: continue

            texts_to_embed = []
            metadata_batch = []
            ids_batch = []
            # Use enumerate to get index within the overall chunk list for unique ID generation
            for local_idx, chunk in enumerate(batch_chunks):
                # Basic validation already done in load_chunk_data, but double check keys
                if not all(k in chunk for k in ('store', 'category', 'chunk_text')):
                    logging.warning(f"Skipping invalid chunk in batch {i//BATCH_SIZE} (missing keys): {chunk}")
                    continue

                chunk_text = chunk['chunk_text']
                store = chunk['store']
                category = chunk['category']

                texts_to_embed.append(chunk_text)
                # Generate a unique ID based on store, category, and global index i
                # Using i+local_idx ensures uniqueness even if batches are small
                chunk_id = f"{store}-{category}-{i+local_idx}"
                ids_batch.append(chunk_id)
                # Store relevant info in metadata
                metadata_batch.append({'store': store, 'category': category, 'original_chunk': chunk_text})

            if not texts_to_embed: continue

            # Generate embeddings for the batch of chunk texts
            embeddings_batch = generate_embeddings(openai_client, texts_to_embed)

            if len(ids_batch) == len(embeddings_batch) == len(metadata_batch):
                vectors_to_upsert = list(zip(ids_batch, embeddings_batch, metadata_batch))
                upsert_batch(index, vectors_to_upsert)
                total_chunks_processed += len(vectors_to_upsert)
            else:
                logging.error(f"Batch length mismatch for index {i}: IDs={len(ids_batch)}, Embeds={len(embeddings_batch)}, Meta={len(metadata_batch)}. Skipping batch.")

    except Exception as batch_proc_e:
         logging.error(f"An error occurred during batch processing: {batch_proc_e}")

    finally:
        # Get final stats after processing
        try:
            final_stats = index.describe_index_stats()
            logging.info(f"Final Index '{INDEX_NAME}' stats: {final_stats}")
        except Exception as stats_e:
            logging.warning(f"Could not get final stats for index '{INDEX_NAME}': {stats_e}")

        # Clean up Pinecone client connection
        if pc:
            del pc
            logging.debug(f"Pinecone client object for {INDEX_NAME} deleted.")


    end_time = time.time()
    logging.info(f"\nScript finished in {end_time - start_time:.2f} seconds. Total chunks processed and attempted upsert: {total_chunks_processed}.")

if __name__ == "__main__":
    main()
