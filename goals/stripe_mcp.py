from typing import List

from models.tool_definitions import AgentGoal
from shared.mcp_config import get_stripe_mcp_server_definition

starter_prompt_generic = "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job."

goal_mcp_stripe = AgentGoal(
    id="goal_mcp_stripe",
    category_tag="mcp-integrations",
    agent_name="Stripe MCP Agent",
    agent_friendly_description="Manage Stripe operations via MCP",
    tools=[],  # Will be populated dynamically
    mcp_server_definition=get_stripe_mcp_server_definition(included_tools=[]),
    description="Help manage Stripe operations for customer and product data by using the customers.read and products.read tools.",
    starter_prompt="Welcome! I can help you read Stripe customer and product information.",
    example_conversation_history="\n ".join(
        [
            "agent: Welcome! I can help you read Stripe customer and product information. What would you like to do first?",
            "user: what customers are there?",
            "agent: I'll check for customers now.",
            "user_confirmed_tool_run: <user clicks confirm on customers.read tool>",
            'tool_result: { "customers": [{"id": "cus_abc", "name": "Customer A"}, {"id": "cus_xyz", "name": "Customer B"}] }',
            "agent: I found two customers: Customer A and Customer B. Can I help with anything else?",
            "user: what products exist?",
            "agent: Let me get the list of products for you.",
            "user_confirmed_tool_run: <user clicks confirm on products.read tool>",
            'tool_result: { "products": [{"id": "prod_123", "name": "Gold Plan"}, {"id": "prod_456", "name": "Silver Plan"}] }',
            "agent: I found two products: Gold Plan and Silver Plan.",
        ]
    ),
)


mcp_goals: List[AgentGoal] = [
    goal_mcp_stripe,
]
