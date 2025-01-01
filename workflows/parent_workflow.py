from temporalio import workflow
from .tool_workflow import ToolWorkflow, CombinedInput, ToolWorkflowParams


@workflow.defn
class ParentWorkflow:
    @workflow.run
    async def run(self, some_input: dict) -> dict:
        combined_input = CombinedInput(
            tool_params=ToolWorkflowParams(None, None), tools_data=some_input
        )
        child = workflow.start_child_workflow(ToolWorkflow.run, combined_input)
        result = await child
        return result
