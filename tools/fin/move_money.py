import asyncio
import json
import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError

from shared.config import get_temporal_client

# enums for the java enum
# class ExecutionScenarios(Enum):
#     HAPPY_PATH = 0
#     ADVANCED_VISIBILITY = auto() # 1
#     HUMAN_IN_LOOP = auto()       # 2
#     API_DOWNTIME = auto()        # 3
#     BUG_IN_WORKFLOW = auto()     # 4
#     INVALID_ACCOUNT = auto()     # 5


# these dataclasses are for calling the Temporal Workflow
# Python equivalent of the workflow we're calling's Java WorkflowParameterObj
@dataclass
class MoneyMovementWorkflowParameterObj:
    amount: int  # Using snake_case as per Python conventions
    scenario: str


# this is made to demonstrate functionality but it could just as durably be an API call
# this assumes it's a valid account - use check_account_valid() to verify that first
async def move_money(args: dict) -> dict:
    account_key = args.get("email_address_or_account_ID")
    account_type: str = args.get("accounttype")
    amount = args.get("amount")
    destinationaccount = args.get("destinationaccount")

    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "customer_account_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    with open(file_path, "r") as file:
        data = json.load(file)
    account_list = data["accounts"]

    for account in account_list:
        if account["email"] == account_key or account["account_id"] == account_key:
            amount_str: str = str(amount)
            from_account_combo = account_key + account_type

            transfer_workflow_id = await start_workflow(
                amount_cents=str_dollars_to_cents(amount_str),
                from_account_name=from_account_combo,
                to_account_name=destinationaccount,
            )

            if account_type.casefold() == "checking":
                from_key = "checking_balance"
            elif account_type.casefold() == "savings":
                from_key = "savings_balance"
            else:
                return_msg = "Money order for account types other than checking or savings is not implemented."
                return {"error": return_msg}

            to_key = (
                "savings_balance"
                if destinationaccount.casefold() == "savings"
                else "checking_balance"
            )

            # Update from-account balance
            from_balance = float(str_dollars_to_cents(str(account[from_key])))
            from_balance -= float(str_dollars_to_cents(amount_str))
            account[from_key] = str(from_balance / 100)

            # Update destination-account balance
            to_balance = float(str_dollars_to_cents(str(account[to_key])))
            to_balance += float(str_dollars_to_cents(amount_str))
            account[to_key] = str(to_balance / 100)

            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)

            return {
                "status": "money movement complete",
                "confirmation id": transfer_workflow_id,
                "new_balance": account[from_key],
                "destination_balance": account[to_key],
            }

    return_msg = "Account not found with for " + account_key
    return {"error": return_msg}


# Async function to start workflow
async def start_workflow(
    amount_cents: int, from_account_name: str, to_account_name: str
) -> str:
    start_real_workflow = os.getenv("FIN_START_REAL_WORKFLOW")
    if start_real_workflow is not None and start_real_workflow.lower() == "false":
        START_REAL_WORKFLOW = False
    else:
        START_REAL_WORKFLOW = True

    if START_REAL_WORKFLOW:
        # Connect to Temporal
        client = await get_temporal_client()
        # Create the parameter object
        params = MoneyMovementWorkflowParameterObj(
            amount=amount_cents, scenario="HAPPY_PATH"
        )

        workflow_id = (
            "TRANSFER-ACCT-" + from_account_name + "-TO-" + to_account_name
        )  # business-relevant workflow ID

        try:
            handle = await client.start_workflow(
                "moneyTransferWorkflow",  # Workflow name
                params,  # Workflow parameters
                id=workflow_id,
                task_queue="MoneyTransferJava",  # Task queue name
            )
            return handle.id
        except WorkflowAlreadyStartedError as e:
            existing_handle = client.get_workflow_handle(workflow_id=workflow_id)
            return existing_handle.id
    else:
        return (
            "TRANSFER-ACCT-" + from_account_name + "-TO-" + to_account_name + "not-real"
        )


# cleans a string dollar amount description to cents value
def str_dollars_to_cents(dollar_str: str) -> int:
    try:
        # Remove '$' and any whitespace
        cleaned_str = dollar_str.replace("$", "").strip()

        # Handle empty string or invalid input
        if not cleaned_str:
            raise ValueError("Empty amount provided")

        # Convert to float and then to cents
        amount = float(cleaned_str)
        if amount < 0:
            raise ValueError("Negative amounts not allowed")

        return int(amount * 100)
    except ValueError as e:
        raise ValueError(f"Invalid dollar amount format: {dollar_str}") from e
