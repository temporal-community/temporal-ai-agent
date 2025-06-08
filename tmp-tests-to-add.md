Tests you may want to consider for the new features in this diff:

### **1\. MCP Integration and Tooling Tests**

The biggest change is the MCP integration. It's crucial to test the connection, execution, and failure modes of this new component.

* **Test Successful MCP Tool Loading:**

  * **Goal:** Verify that when a workflow is initiated with a goal containing an `mcp_server_definition`, the workflow correctly calls the `mcp_list_tools` activity and dynamically adds the returned tools to its internal tool list.  
  * **Implementation:** Create a workflow test that uses a mock `goal_mcp_stripe`. Mock the `mcp_list_tools` activity to return a predefined list of tools. Assert that the `self.goal.tools` list inside the workflow contains both the original native tools and the new mocked MCP tools after initialization.  
* **Test MCP Tool Execution Flow:**

  * **Goal:** Ensure the `dynamic_tool_activity` correctly identifies an MCP tool and passes the `server_definition` in its arguments.  
  * **Implementation:** In a workflow test, have the mocked `agent_toolPlanner` return an MCP tool (e.g., `list_products`). The test's mocked `dynamic_tool_activity` should assert that the arguments it receives contain the `server_definition` dictionary.  
* **Test MCP Server Connection Failure:**

  * **Goal:** Ensure the workflow handles a failure during the initial `mcp_list_tools` call gracefully.  
  * **Implementation:** Configure the mock `mcp_list_tools` activity to raise an `ActivityError` or return a `{"success": False}` payload. The workflow should catch this, log the error, and continue execution without the MCP tools. The agent's next response should reflect that the external tools are unavailable.  
* **Test Individual MCP Tool Execution Failure:**

  * **Goal:** Verify the system's behavior when a single MCP tool call fails.  
  * **Implementation:** In a workflow test, have the agent attempt to run an MCP tool. The mock for `dynamic_tool_activity` should return a `{"success": False, "error": "Connection timed out"}` payload. Assert that this error is recorded in the workflow's `tool_results` and that the agent can formulate a response acknowledging the failure.  
* **Test Argument Type Conversion (`_convert_args_types`):**

  * **Goal:** Create a dedicated unit test for this new private helper function in `tool_activities.py`.  
  * **Implementation:** Test that it correctly converts string values like `"123"`, `"123.45"`, `"true"`, and `"false"` to their respective `int`, `float`, and `bool` types, while leaving other strings and data types unchanged.

---

### **2\. Food Ordering Goal (End-to-End Workflow)**

The new `goal_food_ordering` is your most complex use case, mixing native and MCP tools. A full end-to-end test is essential.

* **Test Full Conversation Flow:**

  * **Goal:** Simulate the entire user conversation outlined in the `example_conversation_history` for the `goal_food_ordering`.  
  * **Implementation:** This requires a more advanced workflow test where the `agent_toolPlanner` mock is stateful. It should return a specific tool based on the last message in the conversation history. For example:  
    1. Initial prompt \-\> `list_products` (MCP)  
    2. User selects pizza \-\> `list_prices` (MCP)  
    3. User provides email \-\> `AddToCart` (Native)  
    4. User wants to check out \-\> `create_customer` (MCP)  
    5. ...and so on, until `finalize_invoice` (MCP) is called.  
  * This test will validate the agent's ability to chain different tool types and carry context across multiple turns.  
* **Test `create_invoice_item` Logic:**

  * **Goal:** The goal description specifically notes that `create_invoice_item` must be called for each item instance (e.g., twice for two pizzas). This is a critical piece of business logic to test.  
  * **Implementation:** Within the end-to-end test above, when the user orders "2 pepperoni pizzas," assert that the `dynamic_tool_activity` for `create_invoice_item` is executed exactly twice with the correct `price` argument.

---

### **3\. Native `AddToCart` Tool Tests**

* **Test Input Validation:**  
  * **Goal:** Create unit tests for the new `add_to_cart` native tool.  
  * **Implementation:** Write separate tests that call `add_to_cart` with invalid arguments (e.g., `quantity=0`, `item_price=-5`, `customer_email=None`) and assert that it returns the expected error dictionary for each case.

---

### **4\. Core Logic & Refactoring Tests**

* **Test `is_mcp_tool` Helper Function:**

  * **Goal:** Unit test the logic that differentiates native from MCP tools in `workflow_helpers.py`.  
  * **Implementation:** Create a test that calls `is_mcp_tool` with various tool names. Assert it returns `False` for known native tools (`AddToCart`, `ListAgents`) and `True` for tools you expect to come from an MCP server (`list_products`, `create_customer`).  
* **Test Prompt Generation with MCP Context:**

  * **Goal:** Ensure the LLM prompt correctly includes information about available MCP tools.  
  * **Implementation:** Unit test `generate_genai_prompt`. Call it with a mock `mcp_tools_info` dictionary. Assert that the resulting prompt string contains the `=== MCP Server Information ===` section and lists the tools from the mock data. Also test the case where `mcp_tools_info` indicates a failure.

