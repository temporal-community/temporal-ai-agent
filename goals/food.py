from typing import List

import tools.tool_registry as tool_registry
from models.tool_definitions import AgentGoal
from shared.mcp_config import get_stripe_mcp_server_definition

starter_prompt_generic = "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job."

goal_food_ordering = AgentGoal(
    id="goal_food_ordering",
    category_tag="food",
    agent_name="Food Ordering Assistant",
    agent_friendly_description="Order food from Tony's Pizza Palace using Stripe for payment processing. Browse menu, add items to your order, and check out securely. Please ensure context carries over between tool runs.",
    tools=[tool_registry.food_add_to_cart_tool],
    mcp_server_definition=get_stripe_mcp_server_definition(
        included_tools=[
            "list_products",
            "list_prices",
            "create_customer",
            "create_invoice",
            "create_invoice_item",
            "finalize_invoice",
        ]
    ),
    description="The user wants to order food from Tony's Pizza Palace. "
    "First, help the user browse the menu by calling list_products. "
    "When they express interest in items, get pricing using list_prices. "
    "Add items to their cart using AddToCart as they decide - the order doesn't matter, multiple items can be added. "
    "After they're done selecting items, get their customer details and create a Stripe customer. "
    "For checkout: 1) create_invoice, 2) create_invoice_item for each individual item (IMPORTANT: create_invoice_item does NOT accept quantity parameter - call it once per item, so if user wants 2 pizzas, call create_invoice_item twice with the same price), "
    "3) finalize_invoice. The finalized invoice will contain a hosted_invoice_url for payment.",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I want to order food.",
            "agent: Welcome to Tony's Pizza Palace! I can help you browse our menu, add items to your cart, and process payment. Let me show you what we have available.",
            "user_confirmed_tool_run: <user clicks confirm on list_products tool with limit=100 and product.metadata.use_case == 'food_ordering_demo'>",
            'tool_result: {"products": [{"id": "prod_pepperoni", "name": "Pepperoni Pizza", "description": "A timeless classic featuring pepperoni", "images": ["https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfcGRHc0c4cEZYWmR2bm0zOHBOa0FWMk5t008QmCJoWr"]}, {"id": "prod_margherita", "name": "Margherita Pizza", "description": "Fresh mozzarella and basil", "images": ["https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfamdmTXBFbzY0TW9rS2N0c2g0Tml2SERL00Evl60Ttq"]}, {"id": "prod_garlic_bread", "name": "Garlic Bread", "description": "Warm crusty bread with garlic butter", "images": ["https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfWTdIZTBkUjNZNFQ1ZEhSVG9nRnduY1pS00XVgLRRZD"]}, {"id": "prod_soda", "name": "Soda", "description": "A large bottle of cola", "images": ["https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfbDJxckJKMDRnT1dDc243OHlZNWNkZkY5006Xg07kHT"]}]}',
            "agent: Welcome to our menu! Here's what we have available:\\n\\n**Pepperoni Pizza** - A timeless classic featuring pepperoni\\n![Pepperoni Pizza](https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfcGRHc0c4cEZYWmR2bm0zOHBOa0FWMk5t008QmCJoWr)\\n\\n**Margherita Pizza** - Fresh mozzarella and basil\\n![Margherita Pizza](https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfamdmTXBFbzY0TW9rS2N0c2g0Tml2SERL00Evl60Ttq)\\n\\n**Garlic Bread** - Warm crusty bread with garlic butter\\n![Garlic Bread](https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfWTdIZTBkUjNZNFQ1ZEhSVG9nRnduY1pS00XVgLRRZD)\\n\\n**Soda** - A large bottle of cola\\n![Soda](https://files.stripe.com/links/MDB8YWNjdF8xTkJPTHVLVlpienc3UUE1fGZsX3Rlc3RfbDJxckJKMDRnT1dDc243OHlZNWNkZkY5006Xg07kHT)\\n\\nWhat would you like to order?",
            "user: I'd like 2 pepperoni pizzas and a soda.",
            "agent: Excellent! Let me get the pricing for the pepperoni pizzas first so you know the cost.",
            "user_confirmed_tool_run: <user clicks confirm on list_prices tool with product='prod_pepperoni'>",
            'tool_result: {"prices": [{"id": "price_pepperoni_large", "product": "prod_pepperoni", "unit_amount": 2299, "currency": "usd"}]}',
            "agent: Pepperoni Pizza is $22.99 each. Now let me check the soda pricing:",
            "user_confirmed_tool_run: <user clicks confirm on list_prices tool with product='prod_soda'>",
            'tool_result: {"prices": [{"id": "price_soda", "product": "prod_soda", "unit_amount": 250, "currency": "usd"}]}',
            "agent: And Soda is $2.50. So 2 Pepperoni Pizzas ($22.99 each) plus 1 Soda ($2.50) = $48.48 total. What's your email address to add these items to your cart?",
            "user: jane.smith@example.com",
            "agent: Perfect! Adding 2 Pepperoni Pizzas to your cart for jane.smith@example.com. Note: I'm using quantity=2 since you want 2 pizzas.",
            "user_confirmed_tool_run: <user clicks confirm on AddToCart tool with customer_email='jane.smith@example.com', item_name='Pepperoni Pizza', item_price=22.99, quantity=2, stripe_product_id='prod_pepperoni'>",
            'tool_result: {"status": "success", "message": "Added 2 x Pepperoni Pizza ($22.99) to cart for jane.smith@example.com", "item_added": {"quantity": 2, "name": "Pepperoni Pizza"}}',
            "agent: Great! Added 2 Pepperoni Pizzas to your cart. Now adding the Soda (quantity=1):",
            "user_confirmed_tool_run: <user clicks confirm on AddToCart tool with customer_email='jane.smith@example.com', item_name='Soda', item_price=2.50, quantity=1, stripe_product_id='prod_soda'>",
            'tool_result: {"status": "success", "message": "Added 1 x Soda ($2.50) to cart for jane.smith@example.com", "item_added": {"quantity": 1, "name": "Soda"}}',
            "agent: Perfect! Added 1 Soda to your cart. Your cart now contains: 2 Pepperoni Pizzas ($22.99 each) and 1 Soda ($2.50). What else would you like to order?",
            "user: Nothing, that's all.",
            "agent: Great! Your order is complete with 2 Pepperoni Pizzas and 1 Soda for a total of $48.48. Now let's proceed to checkout. I'll need your full name to create your customer profile.",
            "user: My name is Jane Smith.",
            "agent: Thank you Jane! Creating your Stripe customer profile with name and email.",
            "user_confirmed_tool_run: <user clicks confirm on create_customer tool with name='Jane Smith' and email='jane.smith@example.com'>",
            'tool_result: {"customer": {"id": "cus_ExAmPlE12345", "name": "Jane Smith", "email": "jane.smith@example.com"}}',
            "agent: Customer profile created! Now I'll create a draft invoice for your order.",
            "user_confirmed_tool_run: <user clicks confirm on create_invoice tool with customer='cus_ExAmPlE12345'>",
            'tool_result: {"invoice": {"id": "in_InvOicE54321", "status": "draft", "customer": "cus_ExAmPlE12345"}}',
            "agent: Invoice created! Now adding your first Pepperoni Pizza to the invoice.",
            "user_confirmed_tool_run: <user clicks confirm on create_invoice_item tool with customer='cus_ExAmPlE12345', invoice='in_InvOicE54321', price='price_pepperoni_large'>",
            'tool_result: {"status": "success", "invoice_item": {"id": "ii_pizza1"}}',
            "agent: First pizza added! Now adding your second Pepperoni Pizza to the invoice.",
            "user_confirmed_tool_run: <user clicks confirm on create_invoice_item tool with customer='cus_ExAmPlE12345', invoice='in_InvOicE54321', price='price_pepperoni_large'>",
            'tool_result: {"status": "success", "invoice_item": {"id": "ii_pizza2"}}',
            "agent: Both pizzas added! Now adding your Soda to the invoice.",
            "user_confirmed_tool_run: <user clicks confirm on create_invoice_item tool with customer='cus_ExAmPlE12345', invoice='in_InvOicE54321', price='price_soda'>",
            'tool_result: {"status": "success", "invoice_item": {"id": "ii_soda"}}',
            "agent: All items added to invoice! Now finalizing to generate the payment link.",
            "user_confirmed_tool_run: <user clicks confirm on finalize_invoice tool with invoice='in_InvOicE54321'>",
            'tool_result: {"invoice": {"id": "in_InvOicE54321", "status": "open", "hosted_invoice_url": "https://invoice.stripe.com/i/acct_1NBOLuKVZbzw7QA5/test_YWNjdF8xTkJPTHVLVlpienc3UUE1LF9SbGJlZ2xLMjhlc3lxNzFkVVBXbkswOUlFa2Rna1RxLDEzMDAwMTY4Nw0200RKeJRMlw?s=ap", "amount_due": 4848}}',
            "agent: Perfect! Your order is complete with 2 Pepperoni Pizzas and 1 Soda. Total: $48.48. Pay securely here: https://invoice.stripe.com/i/acct_1NBOLuKVZbzw7QA5/test_YWNjdF8xTkJPTHVLVlpienc3UUE1LF9SbGJlZ2xLMjhlc3lxNzFkVVBXbkswOUlFa2Rna1RxLDEzMDAwMTY4Nw0200RKeJRMlw?s=ap\\\\n\\\\nThank you for ordering from Tony's Pizza Palace!",
        ]
    ),
)

food_goals: List[AgentGoal] = [
    goal_food_ordering,
]
