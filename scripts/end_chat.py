import asyncio


from workflows.agent_goal_workflow import AgentGoalWorkflow


async def main():
    # Create client connected to server at the given address
    client = await Client.connect("localhost:7233")

    workflow_id = "agent-workflow"

    handle = client.get_workflow_handle_for(AgentGoalWorkflow.run, workflow_id)

    # Sends a signal to the workflow
    await handle.signal(AgentGoalWorkflow.end_chat)


if __name__ == "__main__":
    print("Sending signal to end chat.")
    asyncio.run(main())
