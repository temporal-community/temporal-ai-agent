import asyncio

from shared.config import get_temporal_client
from workflows.agent_goal_workflow import AgentGoalWorkflow


async def main():
    # Create client connected to server at the given address
    client = await get_temporal_client()
    workflow_id = "agent-workflow"

    handle = client.get_workflow_handle(workflow_id)

    # Queries the workflow for the conversation history
    history = await handle.query(AgentGoalWorkflow.get_conversation_history)

    print("Conversation History")
    print(history)


if __name__ == "__main__":
    asyncio.run(main())
