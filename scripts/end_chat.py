import asyncio

from shared.config import get_temporal_client
from workflows.agent_goal_workflow import AgentGoalWorkflow


async def main():
    # Create client connected to server at the given address
    client = await get_temporal_client()

    workflow_id = "agent-workflow"

    handle = client.get_workflow_handle_for(AgentGoalWorkflow.run, workflow_id)

    # Sends a signal to the workflow
    await handle.signal(AgentGoalWorkflow.end_chat)


if __name__ == "__main__":
    print("Sending signal to end chat.")
    asyncio.run(main())
