import asyncio
import concurrent.futures
import logging
import os

from dotenv import load_dotenv
from temporalio.worker import Worker

from activities.tool_activities import ToolActivities, dynamic_tool_activity
from shared.config import TEMPORAL_TASK_QUEUE, get_temporal_client
from workflows.agent_goal_workflow import AgentGoalWorkflow


async def main():
    # Load environment variables
    load_dotenv(override=True)

    # Print LLM configuration info
    llm_model = os.environ.get("LLM_MODEL", "openai/gpt-4")
    print(f"Worker will use LLM model: {llm_model}")

    # Create the client
    client = await get_temporal_client()

    # Initialize the activities class
    activities = ToolActivities()
    print(f"ToolActivities initialized with LLM model: {llm_model}")

    # If using Ollama, pre-load the model to avoid cold start latency
    if llm_model.startswith("ollama"):
        print("\n======== OLLAMA MODEL INITIALIZATION ========")
        print("Ollama models need to be loaded into memory on first use.")
        print("This may take 30+ seconds depending on your hardware and model size.")
        print("Please wait while the model is being loaded...")

        # This call will load the model and measure initialization time
        success = activities.warm_up_ollama()

        if success:
            print("===========================================================")
            print("✅ Ollama model successfully pre-loaded and ready for requests!")
            print("===========================================================\n")
        else:
            print("===========================================================")
            print("⚠️ Ollama model pre-loading failed. The worker will continue,")
            print("but the first actual request may experience a delay while")
            print("the model is loaded on-demand.")
            print("===========================================================\n")

    print("Worker ready to process tasks!")
    logging.basicConfig(level=logging.WARN)

    # Run the worker
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue=TEMPORAL_TASK_QUEUE,
            workflows=[AgentGoalWorkflow],
            activities=[
                activities.agent_validatePrompt,
                activities.agent_toolPlanner,
                activities.get_wf_env_vars,
                dynamic_tool_activity,
            ],
            activity_executor=activity_executor,
        )

        print(f"Starting worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
