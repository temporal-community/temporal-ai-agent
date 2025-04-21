from datetime import date, timedelta
import os
from pathlib import Path
import json
from temporalio.client import (
    Client,
    WithStartWorkflowOperation,
    WorkflowHandle,
    WorkflowUpdateFailedError,
)
from temporalio import common
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
    sourceAccount: str
    targetAccount: str

@dataclass
class TxResult:
    transactionId: str
    status: str

#demonstrate starting a workflow and early return pattern while the workflow continues
async def submit_loan_application(args: dict) -> dict:
    account_key = args.get("email_address_or_account_ID")
    amount = args.get("amount")

    loan_status: dict = await start_workflow(amount=amount,account_name=account_key)

    if loan_status.get("error") is None:
        return {'status': loan_status.get("loan_application_status"), 'detailed_status': loan_status.get("application_details"), 'next_step': loan_status.get("advisement"), 'confirmation_id': loan_status.get("transaction_id")}  
    else:
        print(loan_status)
        return loan_status
    

# Async function to start workflow
async def start_workflow(amount: str, account_name: str, )-> dict:
 
    # Connect to Temporal 
    client = await get_temporal_client()
    start_real_workflow = os.getenv("FIN_START_REAL_WORKFLOW")
    if start_real_workflow is not None and start_real_workflow.lower() == "false":
        START_REAL_WORKFLOW = False
        return {'loan_application_status': "applied", 'application_details': "loan application is submitted and initial validation is complete",'transaction_id': "APPLICATION"+account_name, 'advisement': "You'll receive a confirmation for final approval in three business days", }  
    else:
        START_REAL_WORKFLOW = True
    
        # Define the workflow ID and task queue
        workflow_id = "LOAN_APPLICATION-"+account_name+"-"+date.today().strftime('%Y-%m-%d')
        task_queue = "LatencyOptimizationTEST"

        # Create a TransactionRequest (matching the Java workflow's expected input)
        tx_request = TransactionRequest(
            amount=float(amount),
            targetAccount=account_name,
            sourceAccount=account_name,
        )

        start_op = WithStartWorkflowOperation(
            "TransactionWorkflowLocalBeforeUpdate",
            tx_request,
            id=workflow_id,
            id_conflict_policy=common.WorkflowIDConflictPolicy.USE_EXISTING,
            task_queue=task_queue,
        )

        try:
            print("trying update-with-start")
            tx_result = TxResult(
                await client.execute_update_with_start_workflow(
                    "returnInitResult",
                    start_workflow_operation=start_op,
                )
            )
        except WorkflowUpdateFailedError:
            print("aww man got exception WorkflowUpdateFailedError" )
            tx_result = None
            return_msg = "Loan could not be processed for " + account_name
            return {"error": return_msg}

        workflow_handle = await start_op.workflow_handle()
        print(tx_result)

        print(f"Update result: Transaction ID = {tx_result.transactionId}, Message = {tx_result.status}")

        # Optionally, wait for the workflow to complete and get the final result
        # final_result = await handle.result()
        # print(f"Workflow completed with result: {final_result}")


        # return {'status': loan_status.get("loan_status"), 'detailed_status': loan_status.get("results"), 'next_step': loan_status.get("advisement"), 'confirmation_id': loan_status.get("workflowID")}  
        return {'loan_application_status': "applied", 'application_details': "loan application is submitted and initial validation is complete",'transaction_id': tx_result.transactionId, 'advisement': "You'll receive a confirmation for final approval in three business days", }  
    