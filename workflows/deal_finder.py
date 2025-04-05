from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
from typing import List, Dict, Any, TypedDict
import json

# Import activities
with workflow.unsafe.imports_passed_through():
    from activities.deal_finder_activities import DealFinderActivities

# --- Define Input/Output Types (based on TypeScript) ---

class RetrieveItemWorkflowRequest(TypedDict):
    llmEmbeddingModel: str
    llmModel: str
    query: str
    pineconeDBIndexes: List[str]

# Using Dict[str, Any] as placeholder for GroceryItemPineconeDBMetaSchema
GroceryItem = Dict[str, Any]

class StoreResult(TypedDict):
    results: List[GroceryItem]
    collection: str

AllStoreResultsWorkflowResponse = List[StoreResult]

# --- Temporal Activity Configuration ---

# Use timeouts similar to agent_goal_workflow or adjust as needed
ACTIVITY_START_TO_CLOSE_TIMEOUT = timedelta(minutes=5)
ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT = timedelta(minutes=6)
RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=1.5, # Slightly more aggressive backoff than agent_goal
    maximum_attempts=3,
)

# Helper dictionary for common activity options
activity_options = {
    "start_to_close_timeout": ACTIVITY_START_TO_CLOSE_TIMEOUT,
    "schedule_to_close_timeout": ACTIVITY_SCHEDULE_TO_CLOSE_TIMEOUT,
    "retry_policy": RETRY_POLICY,
}

# --- Helper Functions ---

def parse_price(price_str: Any) -> float:
    """Helper to safely parse price string into number, defaulting to Infinity if invalid."""
    if not isinstance(price_str, str):
        return float('inf')
    cleaned = ''.join(filter(lambda char: char.isdigit() or char == '.', price_str))
    try:
        parsed = float(cleaned)
        return parsed
    except ValueError:
        return float('inf')

def sort_items_by_price(items: List[GroceryItem]) -> List[GroceryItem]:
    """Sorting function (low to high)."""
    # Filter out items without a 'price' key before sorting
    items_with_price = [item for item in items if item and 'price' in item]
    return sorted(items_with_price, key=lambda item: parse_price(item.get('price', 'inf')))

# --- Workflow Definition ---

@workflow.defn
class DealFinderWorkflow:
    @workflow.run
    async def dealFinderItem(self, request: RetrieveItemWorkflowRequest) -> AllStoreResultsWorkflowResponse:
        workflow.logger.info(f"Starting DealFinderWorkflow for query: {request['query']}")

        llm_embedding_model = request['llmEmbeddingModel']
        llm_model = request['llmModel']
        query = request['query']
        pinecone_db_indexes = request['pineconeDBIndexes']

        indexes_data = []

        # 1. Get Pinecone Indexes
        workflow.logger.info(f"Retrieving indexes: {pinecone_db_indexes}")
        for index_name in pinecone_db_indexes:
            try:
                index_obj = await workflow.execute_activity(
                    DealFinderActivities.pinecone_get_index,
                    args=[index_name],
                    **activity_options
                )
                indexes_data.append({
                    "pineconeDBIndex": index_name,
                    "index": index_obj
                })
                workflow.logger.info(f"Successfully retrieved index: {index_name}")
            except Exception as e:
                workflow.logger.error(f"Failed to get index {index_name}: {e}")
                # Decide how to handle failure: skip index, fail workflow, etc.
                # Here, we'll just log and skip this index.
                continue

        # 2. Get Query Embedding
        workflow.logger.info(f"Generating embedding for query: {query}")
        embedding_result = await workflow.execute_activity(
            DealFinderActivities.ollama_embed,
            args=[llm_embedding_model, query],
            **activity_options
        )
        query_embedding = embedding_result['embeddings']

        # 3. Query each index
        workflow.logger.info("Querying indexes with embedding...")
        query_results = []
        for data in indexes_data:
            try:
                query_response = await workflow.execute_activity(
                    DealFinderActivities.pinecone_query,
                    args=[data['index'], query_embedding], # Pass args as a list
                    # Assuming default n_results=10 is acceptable, or pass explicitly:
                    # args=[data['index'], query_embedding, 10],
                    **activity_options
                )
                # The stub returns empty lists, so these will be empty in testing
                possible_items = query_response.get('documents', [[]])[0]
                metadata = query_response.get('metadatas', [[]])[0]
                query_results.append({
                    **data,
                    "metadata": metadata,
                    "possibleItems": possible_items
                })
                workflow.logger.info(f"Query successful for index: {data['pineconeDBIndex']}")
            except Exception as e:
                workflow.logger.error(f"Failed to query index {data['pineconeDBIndex']}: {e}")
                # Skip this index on query failure
                continue
        indexes_data = query_results

        # 4. Process results with LLM and refine
        workflow.logger.info("Processing results with LLM...")
        final_results_per_index: AllStoreResultsWorkflowResponse = []

        for data in indexes_data:
            index_name = data['pineconeDBIndex']
            possible_items = data.get('possibleItems', [])
            metadata_list = data.get('metadata', []) # This is expected to be List[GroceryItem]

            if not possible_items:
                workflow.logger.warn(f"No possible items found from PineconeDB query for index {index_name}. Skipping LLM step.")
                final_results_per_index.append({
                    "results": [],
                    "collection": index_name # Keep 'collection' key for StoreResult compatibility
                })
                continue

            # Construct LLM prompt (similar to TypeScript)
            items_str = "\n- ".join(possible_items)
            llm_prompt = (
                f"You are an AI assistant helping the user find grocery items related to their query. \n"
                f"From the list below, return only the exact strings that are relevant to the query.  \n"
                f"Each string includes both the item name and its deal — do not change or rephrase them. \n"
                f"Respond with an array of the matching strings from the list. If none match, return an empty array.\n"
                f"Grocery items:\n- {items_str}"
            )

            try:
                workflow.logger.info(f"Calling LLM for index: {index_name}")
                llm_response = await workflow.execute_activity(
                    DealFinderActivities.ollama_generate,
                    args=[llm_model, query, llm_prompt, {"type": "array", "items": {"type": "string"}}],
                    # Note: Changed order/inclusion of args to match activity definition (model, prompt, system, format)
                    # prompt=query, system=llm_prompt, format={...}
                    **activity_options
                )
                results_str = llm_response['response']
                filter_results: List[str]

                try:
                    filter_results = json.loads(results_str)
                    workflow.logger.info(f"LLM response parsed successfully for {index_name}")
                except json.JSONDecodeError:
                    workflow.logger.warn(f"LLM response for {index_name} was not valid JSON. Attempting repair...")
                    repaired_json = await workflow.execute_activity(
                        DealFinderActivities.json_repair,
                        args=[results_str],
                         **activity_options
                    )
                    try:
                         filter_results = json.loads(repaired_json)
                         workflow.logger.info(f"JSON repair successful for {index_name}")
                    except json.JSONDecodeError:
                         workflow.logger.error(f"JSON repair failed for {index_name}. Skipping results.")
                         filter_results = []

                # Remove duplicates
                filter_results = list(set(filter_results))

                # Refine results: Find metadata, handle misses with reverse search
                refined_items: List[GroceryItem] = []
                for item_str in filter_results:
                    # Direct find (simplified check)
                    found_item = next((meta for meta in metadata_list if isinstance(meta, dict) and meta.get('name') and item_str in meta['name']), None)

                    if found_item:
                        refined_items.append(found_item)
                    else:
                        workflow.logger.info(f"Item '{item_str}' not found directly in metadata for {index_name}. Attempting reverse search.")
                        # Item Embedding
                        item_embedding_result = await workflow.execute_activity(
                            DealFinderActivities.ollama_embed,
                            args=[llm_embedding_model, item_str],
                             **activity_options
                        )
                        item_embedding = item_embedding_result['embeddings']

                        # Reverse search
                        item_query_response = await workflow.execute_activity(
                            DealFinderActivities.pinecone_query,
                            args=[data['index'], item_embedding, 1], # n_results=1
                            **activity_options
                        )

                        # Assuming metadata is nested [[item]]
                        reverse_found_meta = item_query_response.get('metadatas', [[[]]])[0]
                        if reverse_found_meta and isinstance(reverse_found_meta[0], dict):
                             workflow.logger.info(f"Reverse search found item for '{item_str}' in {index_name}")
                             refined_items.append(reverse_found_meta[0])
                        else:
                            workflow.logger.warn(f"Reverse search failed for item '{item_str}' in {index_name}")
                            # Optionally add a placeholder or skip

                # Sort final items by price
                sorted_results = sort_items_by_price(refined_items)
                workflow.logger.info(f"Processed {len(sorted_results)} items for index {index_name}")
                final_results_per_index.append({
                    "results": sorted_results,
                    "collection": index_name # Keep 'collection' key for StoreResult compatibility
                })

            except Exception as e:
                workflow.logger.error(f"Error processing LLM results for index {index_name}: {e}")
                # Append empty results for this index on error
                final_results_per_index.append({
                    "results": [],
                    "collection": index_name # Keep 'collection' key for StoreResult compatibility
                })

        workflow.logger.info("DealFinderWorkflow finished.")
        return final_results_per_index 