from datetime import timedelta
import os
from pathlib import Path
import json
from temporalio.client import Client, WorkflowHandle
from dataclasses import dataclass
from typing import Optional
import asyncio
from temporalio.exceptions import WorkflowAlreadyStartedError
from shared.config import get_temporal_client


# Define data structures to match the Java workflow's expected input/output
# see https://github.com/temporal-sa/temporal-latency-optimization-scenarios for more details
@dataclass
class TransactionRequest:
    amount: float
    account_id: str

@dataclass
class TxResult:
    transaction_id: str
    message: str

#demonstrate starting a workflow and early return pattern while the workflow continues
async def submit_loan_application(args: dict) -> dict:
    account_key = args.get("accountkey")
    amount = args.get("amount")

    loan_status: dict = await start_workflow(amount=amount,account_name=account_key)

    return {'status': loan_status.get("loan_status"), 'detailed_status': loan_status.get("results"), 'next_step': loan_status.get("advisement"), 'confirmation_id': loan_status.get("workflowID")}  
    

# Async function to start workflow
async def start_workflow(amount: str, account_name: str, )-> dict:
 
    # Connect to Temporal 
    client = await get_temporal_client()
    start_real_workflow = os.getenv("FIN_START_REAL_WORKFLOW")
    if start_real_workflow is not None and start_real_workflow.lower() == "false":
        START_REAL_WORKFLOW = False
    else:
        START_REAL_WORKFLOW = True
    
    if START_REAL_WORKFLOW:

        # Define the workflow ID and task queue
        workflow_id = "APPLICATION-"+account_name
        task_queue = "LatencyOptimizationTEST"

        # Create a TransactionRequest (matching the Java workflow's expected input)
        tx_request = TransactionRequest(
            amount=float(amount),
            account_id=account_name
        )

        #try:
        # Use update-with-start to start the workflow and call the update method
        handle: WorkflowHandle = await client.start_workflow(
            "TransactionWorkflowLocalBeforeUpdate.processTransaction",  # Workflow name
            tx_request,  # Input to the processTransaction method
            id=workflow_id,
            task_queue=task_queue,
            execution_timeout=timedelta(minutes=5),
            # Specify the update to call immediately after starting
            update="returnInitResult",
            update_args=[]  # No arguments needed for returnInitResult
        )

        # Wait for the update result (returnInitResult)
        update_result = await handle.result_of_update("returnInitResult")
        
        # Since the result is a RawValue, we need to deserialize it
        # For simplicity, assuming the result is TxResult (adjust based on actual serialization)
        #result_dict = update_result.payloads[0].decode()  # Simplified; use proper deserialization
        tx_result = TxResult(
            transaction_id=result_dict.get("transaction_id", ""),
            message=result_dict.get("message", "")
        )

        print(f"Update result: Transaction ID = {tx_result.transaction_id}, Message = {tx_result.message}")

        # Optionally, wait for the workflow to complete and get the final result
        # final_result = await handle.result()
        # print(f"Workflow completed with result: {final_result}")

        #except Exception as e:
        #    print(f"Error executing workflow: {e}")


    # return {'status': loan_status.get("loan_status"), 'detailed_status': loan_status.get("results"), 'next_step': loan_status.get("advisement"), 'confirmation_id': loan_status.get("workflowID")}  
    return {'status': "status", 'detailed_status': "loan application is submitted and initial validation is complete",'confirmation id': "11358", 'next_step': "You'll receive a confirmation for final approval in three business days", }  
    