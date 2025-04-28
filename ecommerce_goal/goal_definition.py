# ----- E-Commerce Goals ---
# this tool checks account balances, and uses ./data/customer_account_data.json as dummy data
goal_ecomm_order_status = AgentGoal(
    id="goal_ecomm_order_status",
    category_tag="ecommerce",
    agent_name="Check Order Status",
    agent_friendly_description="Check the status of your order.",
    tools=[
        tool_registry.ecomm_get_order,
        tool_registry.ecomm_track_package,
    ],
    description="The user wants to learn the status of a specific order. If the status is 'shipped' or 'delivered', they might want to get the package tracking information. To assist with that goal, help the user gather args for these tools in order: "
    "1. GetOrder: get information about an order"
    "2. TrackPackage: provide tracking information for the package. This tool is optional and should only be offered if the status is 'shipped' OR 'delivered' - otherwise, skip this tool and do not mention it to the user.",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to know the status of my order",
            "agent: Sure! I can help you out with that. May I have your order number?",
            "user: 102 ",
            "user_confirmed_tool_run: <user clicks confirm on GetOrderStatus tool>",
            "tool_result: { 'id': '102', 'summary': 'Red Sunglasses', 'email': 'matt.murdock@nelsonmurdock.com', 'status': 'shipped', 'order_date': '2025-04-01', 'last_order_update': '2025-04-06', 'tracking_id': '039813852990618' }",
            "agent: Your order 'Red Sunglasses,' placed April 1, 2025, was shipped on April 6, 2025. Would you like to see the tracking inforation?",
            "user: Yes",
            "user_confirmed_tool_run: <user clicks confirm on TrackPackage tool>",
            "tool_result: { 'scheduled_delivery_date': 'April 30, 2025', 'carrier': 'USPS', 'status_summary': 'Your item has left our acceptance facility and is in transit to a sorting facility on April 10, 2025 at 7:06 am in IRON RIDGE, WI 53035.', 'tracking_link': 'https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1=12345','last_tracking_update': '2025-03-22T16:14:48'}",
            "agent: Your package is scheduled to be delivered on April 30, 2025 via USPS. Here is the most recent status from them regarding your package, updated as of March 22: \n"
            "Your item has left our acceptance facility and is in transit to a sorting facility on April 10, 2025 at 7:06 am in IRON RIDGE, WI 53035. \n"
            "You can find the full tracking details here: tracking_link !",
        ]
    ),
)

goal_ecomm_list_orders = AgentGoal(
    id="goal_ecomm_list_orders",
    category_tag="ecommerce",
    agent_name="List All Orders",
    agent_friendly_description="List all orders for a user.",
    tools=[
        tool_registry.ecomm_list_orders,
        tool_registry.ecomm_get_order,
        tool_registry.ecomm_track_package,
    ],
    description="The user wants to see all of their orders. They may want more details about specific orders, and if the status of an order is 'shipped' or 'delivered', they might want to get the package tracking information. To assist with that goal, help the user gather args for this tool: "
    "1. ListOrders: list orders for a user"
    " and then offer the following tools, in a loop, until the user indicates they are done:"
    "2. GetOrder: get information about an order. This tool is optional."
    "3. TrackPackage: provide tracking information for the package. This tool is optional and should only be offered if the status is 'shipped' OR 'delivered' - otherwise, skip this tool and do not mention it to the user.",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to see all of my orders.",
            "agent: Sure! I can help you out with that. May I have your email address?",
            "user: email is bob.johnson@emailzzz.com ",
            "user_confirmed_tool_run: <user clicks confirm on ListOrders tool>",
            "tool_result: a list of orders including [{'id': '102', 'summary': 'Red Sunglasses', 'email': 'matt.murdock@nelsonmurdock.com', 'status': 'shipped', 'order_date': '2025-04-01', 'last_order_update': '2025-04-06', 'tracking_id': '039813852990618' }, { 'id': '103', 'summary': 'Blue Sunglasses', 'email': 'matt.murdock@nelsonmurdock.com', 'status': 'paid', 'order_date': '2025-04-03', 'last_order_update': '2025-04-07' }]",
            "agent: Your orders are as follows: \n",
            "1. Red Sunglasses, ordered 4/1/2025 \n",
            "2. Blue Sunglasses, ordered 4/3/2025 \n",
            "Would you like more information about any of your orders?"
            "user: Yes, the Red Sunglasses",
            "agent: Your order 'Red Sunglasses,' placed April 1, 2025, was shipped on April 6, 2025. Would you like to see the tracking inforation?",
            "user: Yes",
            "user_confirmed_tool_run: <user clicks confirm on TrackPackage tool>",
            "tool_result: { 'scheduled_delivery_date': 'April 30, 2025', 'carrier': 'USPS', 'status_summary': 'Your item has left our acceptance facility and is in transit to a sorting facility on April 10, 2025 at 7:06 am in IRON RIDGE, WI 53035.', 'tracking_link': 'https://tools.usps.com/go/TrackConfirmAction?qtc_tLabels1=12345','last_tracking_update': '2025-03-22T16:14:48'}",
            "agent: Your package is scheduled to be delivered on April 30, 2025 via USPS. Here is the most recent status from them regarding your package \n, updated as of March 22: \n"
            "Your item has left our acceptance facility and is in transit to a sorting facility on April 10, 2025 at 7:06 am in IRON RIDGE, WI 53035. \n"
            "You can find the full tracking details here: tracking_link ! \n"
            "Would you like more information about any of your other orders?",
            "user: No" "agent: Thanks, and have a great day!",
        ]
    ),
)

goal_list.append(goal_ecomm_list_orders)
goal_list.append(goal_ecomm_order_status)
