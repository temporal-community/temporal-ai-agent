import asyncio
import concurrent.futures
import logging
import os

from dotenv import load_dotenv
from temporalio.worker import Worker

from activities import mcp_dispatcher_registry
from activities.mcp_dispatcher import mcp_tool_dispatcher
from activities.tool_activities import ToolActivities, mcp_list_tools
from shared.config import TEMPORAL_TASK_QUEUE, get_temporal_client
from shared.mcp_client_manager import MCPClientManager
from workflows.agent_goal_workflow import AgentGoalWorkflow
from workflows.mcp_agent_chain_workflow import MCPAgentChainWorkflow


async def main():
    # Load environment variables
    load_dotenv(override=True)

    # Print LLM configuration info
    llm_model = os.environ.get("LLM_MODEL", "openai/gpt-4")
    print(f"Worker will use LLM model: {llm_model}")

    # Create shared MCP client manager and publish it to the dispatcher
    # registry so the dynamic MCP-tool dispatcher activity can reuse pooled
    # connections instead of opening one per call.
    mcp_client_manager = MCPClientManager()
    mcp_dispatcher_registry.set_client_manager(mcp_client_manager)

    # Create the client
    client = await get_temporal_client()

    # Initialize the activities class with injected manager
    activities = ToolActivities(mcp_client_manager)
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
    logging.basicConfig(level=logging.INFO)

    # Run the worker with proper cleanup
    try:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=100
        ) as activity_executor:
            worker = Worker(
                client,
                task_queue=TEMPORAL_TASK_QUEUE,
                workflows=[AgentGoalWorkflow, MCPAgentChainWorkflow],
                activities=[
                    activities.agent_validatePrompt,
                    activities.agent_toolPlanner,
                    activities.get_wf_env_vars,
                    activities.mcp_tool_activity,
                    mcp_tool_dispatcher,
                    mcp_list_tools,
                ],
                activity_executor=activity_executor,
            )

            print(f"Starting worker, connecting to task queue: {TEMPORAL_TASK_QUEUE}")
            await worker.run()
    finally:
        # Cleanup MCP connections when worker shuts down
        await mcp_client_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
