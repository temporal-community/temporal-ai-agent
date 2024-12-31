# Multi-turn chat with Ollama Entity Workflow

Multi-Turn Chat using an Entity Workflow. The workflow runs forever unless explicitly ended. The workflow continues as new after a configurable number of chat turns to keep the prompt size small and the Temporal event history small. Each continued-as-new workflow receives a summary of the conversation history so far for context.

To run, first see `samples-python` [README.md](../../README.md), and `ollama` [README.md](../README.md) for prerequisites specific to this sample. Once set up, run the following from this directory:

1. Run the worker: `poetry run python run_worker.py`
2. In another terminal run the client with a prompt.

    Example: `poetry run python send_message.py 'What animals are marsupials?'`

3. View the worker's output for the response.
4. Give followup prompts by signaling the workflow.

    Example: `poetry run python send_message.py 'Do they lay eggs?'`
5. Get the conversation history summary by querying the workflow.
    
    Example: `poetry run python get_history.py`
6. To end the chat session, run `poetry run python end_chat.py`
