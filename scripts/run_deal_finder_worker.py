import asyncio
import concurrent.futures
from dotenv import load_dotenv

from temporalio.worker import Worker

# Import the Deal Finder workflow and activities
from workflows.deal_finder import DealFinderWorkflow
from activities.deal_finder_activities import DealFinderActivities

from shared.config import get_temporal_client, TEMPORAL_TASK_QUEUE


async def main():
    # Load environment variables
    load_dotenv(override=True)

    # Create the client
    client = await get_temporal_client()

    # Initialize the Deal Finder activities
    # Note: No LLM configuration needed here for now, as per request.
    deal_finder_activities = DealFinderActivities()
    print("DealFinderActivities initialized.")

    # Prepare the list of activity methods from the instance
    activities_list = [
        deal_finder_activities.json_repair,
        deal_finder_activities.ollama_embed,
        deal_finder_activities.ollama_generate,
        deal_finder_activities.pinecone_get_index,
        deal_finder_activities.pinecone_query,
    ]

    print("Worker ready to process DealFinder tasks!")

    # Run the worker
    # Using a ThreadPoolExecutor for activities. Adjust max_workers if needed.
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as activity_executor:
        worker = Worker(
            client,
            task_queue=TEMPORAL_TASK_QUEUE,
            workflows=[DealFinderWorkflow],
            # Pass the list of activity methods
            activities=activities_list,
            activity_executor=activity_executor,
        )

        print(f"Starting Deal Finder worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main()) 