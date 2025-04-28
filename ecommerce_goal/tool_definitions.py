# ----- ECommerce Use Case Tools -----
ecomm_list_orders = ToolDefinition(
    name="ListOrders",
    description="Get all orders for a certain email address.",
    arguments=[
        ToolArgument(
            name="email_address",
            type="string",
            description="Email address of user by which to find orders",
        ),
    ],
)

ecomm_get_order = ToolDefinition(
    name="GetOrder",
    description="Get infromation about an order by order ID.",
    arguments=[
        ToolArgument(
            name="order_id",
            type="string",
            description="ID of order to determine status of",
        ),
    ],
)

ecomm_track_package = ToolDefinition(
    name="TrackPackage",
    description="Get tracking information for a package by shipping provider and tracking ID",
    arguments=[
        ToolArgument(
            name="tracking_id",
            type="string",
            description="ID of package to track",
        ),
        ToolArgument(
            name="userConfirmation",
            type="string",
            description="Indication of user's desire to get package tracking information",
        ),
    ],
)

# for __init__.py
# if tool_name == "GetOrder":
#     return get_order
# if tool_name == "TrackPackage":
#     return track_package
# if tool_name == "ListOrders":
#     return list_orders
