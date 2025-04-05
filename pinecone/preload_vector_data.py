import os
import json
import yaml
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


def load_store_data(data_path: str) -> list[dict]:
    """Loads grocery data for a store from a JSON file."""
    logging.info(f"Loading data from {data_path}...")
     # Correct path relative to workspace root
    abs_data_path = os.path.abspath(data_path)
    if not os.path.exists(abs_data_path):
        logging.warning(f"Data file not found at resolved path: {abs_data_path}. Trying relative...")
        # Try relative path from script location if running from pinecone/
        script_dir = os.path.dirname(__file__)
        rel_path = os.path.join(script_dir, '..', data_path) # Go up one level
        abs_data_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_data_path):
             logging.warning(f"Also not found at relative path: {abs_data_path}. Skipping store.")
             return []
        else:
             logging.info(f"Found data at relative path: {abs_data_path}")


    try:
        with open(abs_data_path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON data must be a list of items.")
        logging.info(f"Loaded {len(data)} items.")
        return data
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {abs_data_path}. Skipping this store.")
        return []
    except ValueError as e:
        logging.error(f"Data file structure error ({abs_data_path}): {e}. Skipping this store.")
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
    # Assumes script is in pinecone/ subdir relative to workspace root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    logging.info(f"Workspace root detected as: {workspace_root}")
    # Adjust paths to be relative to workspace root if needed, or use absolute paths
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


    # 3. Load Docker Compose Config
    services = load_config(docker_compose_full_path)


    # 4. Process each store service defined in docker-compose
    total_items_processed = 0
    for service_name, service_config in services.items():
        logging.info(f"\n--- Processing store: {service_name} ---")

        # Extract port
        port = None
        if 'ports' in service_config and service_config['ports']:
            port_mapping = service_config['ports'][0]
            try:
                port = int(port_mapping.split(':')[0])
                logging.info(f"Found host port mapping: {port}")
            except (ValueError, IndexError, TypeError):
                logging.warning(f"Could not parse host port from '{port_mapping}' for {service_name}. Skipping.")
                continue
        else:
            logging.warning(f"No port mapping found for service {service_name}. Skipping.")
            continue

        # Dimension check
        try:
            config_dimension = int(service_config.get('environment', {}).get('DIMENSION'))
            if config_dimension != EMBEDDING_DIMENSION:
                 logging.warning(f"Dimension mismatch for {service_name}. Config: {config_dimension}, Script: {EMBEDDING_DIMENSION}. Using script dimension {EMBEDDING_DIMENSION}.")
        except (ValueError, TypeError):
             logging.warning(f"Could not read or parse DIMENSION from environment for {service_name}. Assuming {EMBEDDING_DIMENSION}.")
        except Exception as e:
             logging.warning(f"Error reading dimension for {service_name}: {e}. Assuming {EMBEDDING_DIMENSION}.")


        # 5. Load Data
        data_file = os.path.join(data_dir_full_path, f"{service_name}.json")
        store_data = load_store_data(data_file)
        if not store_data:
            continue


        # 6. Connect to Pinecone Instance using gRPC client with plaintext
        pinecone_grpc_host = f"localhost:{port}"
        index_name = service_name # Assuming index name matches service name
        logging.info(f"Attempting to connect to Pinecone index '{index_name}' via gRPC (plaintext) at {pinecone_grpc_host}...")

        pc = None
        index = None
        try:
            # Initialize Pinecone gRPC client with plaintext=True for local HTTP connection
            pc = Pinecone(api_key="dummy-key", host=pinecone_grpc_host, plaintext=True)

            # === Bypassing Index Listing/Creation for Local Env ===
            # # Check if index exists. gRPC list_indexes might work differently or not at all on local image
            # try:
            #     available_indexes = pc.list_indexes().names
            #     logging.info(f"Available indexes via gRPC: {available_indexes}")
            #     index_exists = index_name in available_indexes
            # except Exception as list_e:
            #     logging.warning(f"Could not list indexes via gRPC ({list_e}). Assuming index '{index_name}' might exist or needs to be accessed directly.")
            #     # For local dev, often best to assume index exists or is auto-created
            #     index_exists = True # Proceed assuming we can get an index handle
            #
            # if not index_exists:
            #      logging.warning(f"Index '{index_name}' not found via gRPC list_indexes. Attempting creation (might fail if not supported)..." )
            #      try:
            #          metric = service_config.get('environment', {}).get('METRIC', 'cosine').lower()
            #          logging.info(f"Creating index '{index_name}' with dimension {EMBEDDING_DIMENSION} and metric '{metric}' via gRPC...")
            #          # gRPC create_index does not take a 'spec'
            #          pc.create_index(name=index_name, dimension=EMBEDDING_DIMENSION, metric=metric)
            #          time.sleep(10) # Delay for index creation
            #          logging.info(f"Index '{index_name}' creation initiated via gRPC. Verifying access...")
            #          # Re-check or just try to get the index object
            #      except Exception as create_e:
            #          logging.error(f"Failed to create index '{index_name}' via gRPC: {create_e}. Ensure the container creates it automatically or create it manually.")
            #          continue # Skip store if index cannot be accessed/created
            # # else:
            #      # logging.info(f"Index '{index_name}' presumed to exist based on gRPC check or assumption.")
            # === End of Bypassed Block ===

            # Directly attempt to get the index object handle, assuming it exists
            # Also pass the host explicitly here, though it might be redundant
            logging.info(f"Attempting to directly get gRPC index handle for '{index_name}' at host {pinecone_grpc_host}...")
            # KEY CHANGE: Use name=, host=, and grpc_config= to disable TLS for data operations
            index = pc.Index(
                name=index_name,
                host=pinecone_grpc_host,
                grpc_config=GRPCClientConfig(secure=False) # Explicitly disable TLS for data operations
            )
            logging.info(f"Successfully obtained gRPC index handle for '{index_name}'.")
            # Optional: Describe index stats (might work with gRPC handle)
            # try:
            #      stats = index.describe_index_stats()
            #      logging.info(f"Initial Index '{index_name}' stats: {stats}")
            # except Exception as desc_e:
            #      logging.warning(f"Could not describe_index_stats for {index_name}: {desc_e}")

        except Exception as e:
            logging.error(f"Error connecting to or preparing index '{index_name}' via gRPC at {pinecone_grpc_host}: {e}")
            if pc: del pc
            continue

        if not index:
            logging.error(f"Failed to get a valid gRPC index object for '{index_name}'. Skipping upserts.")
            continue

        # 7. Process and Upsert Data in Batches
        logging.info(f"Processing {len(store_data)} items for upsertion into '{index_name}'...")
        store_items_processed = 0
        try:
            for i in tqdm(range(0, len(store_data), BATCH_SIZE), desc=f"Upserting to {service_name}", unit="batch"):
                batch_items = store_data[i : i + BATCH_SIZE]
                if not batch_items: continue

                texts_to_embed = []
                metadata_batch = []
                ids_batch = []
                for idx, item in enumerate(batch_items):
                    if not isinstance(item, dict) or 'name' not in item or 'price' not in item:
                        logging.warning(f"Skipping invalid item in batch {i//BATCH_SIZE}: {item}")
                        continue

                    item_text = f"Product: {item.get('name', 'Unknown')}, Price: {item.get('price', 'N/A')}"
                    texts_to_embed.append(item_text)
                    item_id = str(item.get('name', f"{service_name}-item-{i+idx}"))
                    ids_batch.append(item_id)
                    metadata_batch.append({'name': item.get('name'), 'price': item.get('price'), 'original_text': item_text})

                if not texts_to_embed: continue

                embeddings_batch = generate_embeddings(openai_client, texts_to_embed)

                if len(ids_batch) == len(embeddings_batch) == len(metadata_batch):
                    vectors_to_upsert = list(zip(ids_batch, embeddings_batch, metadata_batch))
                    upsert_batch(index, vectors_to_upsert)
                    store_items_processed += len(vectors_to_upsert)
                else:
                    logging.error(f"Batch length mismatch for {service_name} at index {i}: IDs={len(ids_batch)}, Embeds={len(embeddings_batch)}, Meta={len(metadata_batch)}. Skipping batch.")

        except Exception as batch_proc_e:
             logging.error(f"An error occurred during batch processing for {service_name}: {batch_proc_e}")

        finally:
            try:
                final_stats = index.describe_index_stats()
                logging.info(f"Final Index '{index_name}' stats: {final_stats}")
            except Exception as stats_e:
                logging.warning(f"Could not get final stats for index '{index_name}': {stats_e}")

            logging.info(f"--- Finished processing store: {service_name}. Processed {store_items_processed} items. ---")
            total_items_processed += store_items_processed

        # Clean up Pinecone client connection for the store
        if pc:
            del pc
            logging.debug(f"Pinecone client object for {service_name} deleted.")


    end_time = time.time()
    logging.info(f"\nScript finished in {end_time - start_time:.2f} seconds. Total items processed across all stores: {total_items_processed}.")

if __name__ == "__main__":
    main()
