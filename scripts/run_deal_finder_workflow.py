import asyncio
import uuid
from temporalio.client import Client

# Import the workflow definition and its input type
from workflows.deal_finder import DealFinderWorkflow, RetrieveItemWorkflowRequest

from shared.config import get_temporal_client, TEMPORAL_TASK_QUEUE


async def main():
    # Create a Temporal client
    client = await get_temporal_client()

    # --- Define the input for the DealFinderWorkflow ---
    # Since activities are stubbed, specific model names may not matter yet.
    # Replace with actual desired values when integrating real services.
    workflow_input = RetrieveItemWorkflowRequest(
        llmEmbeddingModel="nomic-embed-text", # Example embedding model
        llmModel="llama3",                # Example LLM
        query="organic avocados",           # Example search query
        # Example PineconeDB index names (e.g., store names)
        pineconeDBIndexes=["store-safeway", "store-trader-joes", "store-whole-foods"]
    )

    # Generate a unique ID for this workflow execution
    workflow_id = f"deal-finder-{uuid.uuid4()}"

    print(f"Starting DealFinderWorkflow with ID: {workflow_id}")
    print(f"Input Query: {workflow_input['query']}")
    print(f"Indexes: {workflow_input['pineconeDBIndexes']}")

    try:
        # Start the workflow execution
        handle = await client.start_workflow(
            DealFinderWorkflow.dealFinderItem, # The workflow run method
            workflow_input,                   # The input arguments
            id=workflow_id,
            task_queue=TEMPORAL_TASK_QUEUE,
        )

        print(f"Workflow started. Waiting for result...")

        # Wait for the workflow to complete and get the result
        result = await handle.result()

        print("\n--- Workflow Result ---")
        # Pretty print the result (assuming it's JSON-serializable like List[Dict])
        import json
        print(json.dumps(result, indent=2))
        print("---------------------")

    except Exception as e:
        print(f"\nError starting or executing workflow: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 