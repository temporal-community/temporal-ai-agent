import os
from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.service import TLSConfig

load_dotenv(override=True)

# Temporal connection settings
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "agent-task-queue")
TEMPORAL_LEGACY_TASK_QUEUE = os.getenv("TEMPORAL_LEGACY_TASK_QUEUE", "agent-task-queue-legacy")

# Authentication settings
TEMPORAL_TLS_CERT = os.getenv("TEMPORAL_TLS_CERT", "")
TEMPORAL_TLS_KEY = os.getenv("TEMPORAL_TLS_KEY", "")
TEMPORAL_API_KEY = os.getenv("TEMPORAL_API_KEY", "")

async def get_temporal_client() -> Client:
    """
    Creates a Temporal client based on environment configuration.
    Supports local server, mTLS, and API key authentication methods.
    """
    # Default to no TLS for local development
    tls_config = False
    print(f"Address: {TEMPORAL_ADDRESS}, Namespace {TEMPORAL_NAMESPACE}")
    print("(If unset, then will try to connect to local server)")

    # Configure mTLS if certificate and key are provided
    if TEMPORAL_TLS_CERT and TEMPORAL_TLS_KEY:
        print(f"TLS cert: {TEMPORAL_TLS_CERT}")
        print(f"TLS key: {TEMPORAL_TLS_KEY}")
        with open(TEMPORAL_TLS_CERT, "rb") as f:
            client_cert = f.read()
        with open(TEMPORAL_TLS_KEY, "rb") as f:
            client_key = f.read()
        tls_config = TLSConfig(
            client_cert=client_cert,
            client_private_key=client_key,
        )

    # Use API key authentication if provided
    if TEMPORAL_API_KEY:
        print(f"API key: {TEMPORAL_API_KEY}")
        return await Client.connect(
            TEMPORAL_ADDRESS,
            namespace=TEMPORAL_NAMESPACE,
            api_key=TEMPORAL_API_KEY,
            tls=True,  # Always use TLS with API key
        )

    # Use mTLS or local connection
    return await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
        tls=tls_config,
    )
