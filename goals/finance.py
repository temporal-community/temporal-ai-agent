from typing import List

import tools.tool_registry as tool_registry
from models.tool_definitions import AgentGoal

starter_prompt_generic = "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job."

goal_fin_check_account_balances = AgentGoal(
    id="goal_fin_check_account_balances",
    category_tag="fin",
    agent_name="Account Balances",
    agent_friendly_description="Check your account balances in Checking, Savings, etc.",
    tools=[
        tool_registry.financial_check_account_is_valid,
        tool_registry.financial_get_account_balances,
    ],
    description="The user wants to check their account balances at the bank or financial institution. To assist with that goal, help the user gather args for these tools in order: "
    "1. FinCheckAccountIsValid: validate the user's account is valid"
    "2. FinCheckAccountBalance: Tell the user their account balance at the bank or financial institution",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to check my account balances",
            "agent: Sure! I can help you out with that. May I have your email address and account number?",
            "user: email is bob.johnson@emailzzz.com ",
            "user_confirmed_tool_run: <user clicks confirm on FincheckAccountIsValid tool>",
            "tool_result: { 'status': account valid }",
            "agent: Great! I can tell you what the your account balances are.",
            "user_confirmed_tool_run: <user clicks confirm on FinCheckAccountBalance tool>",
            "tool_result: { 'name': Matt Murdock, 'email': matt.murdock@nelsonmurdock.com, 'account_id': 11235, 'checking_balance': 875.40, 'savings_balance': 3200.15, 'bitcoin_balance': 0.1378, 'account_creation_date': 2014-03-10 }",
            "agent: Your account balances are as follows: \\n "
            "Checking: $875.40. \\n "
            "Savings: $3200.15. \\n "
            "Bitcoint: 0.1378 \\n "
            "Thanks for being a customer since 2014!",
        ]
    ),
)

goal_fin_move_money = AgentGoal(
    id="goal_fin_move_money",
    category_tag="fin",
    agent_name="Money Movement",
    agent_friendly_description="Initiate money movement.",
    tools=[
        tool_registry.financial_check_account_is_valid,
        tool_registry.financial_get_account_balances,
        tool_registry.financial_move_money,
    ],
    description="The user wants to transfer money in their account at the bank or financial institution. To assist with that goal, help the user gather args for these tools in order: "
    "1. FinCheckAccountIsValid: validate the user's account is valid"
    "2. FinCheckAccountBalance: Tell the user their account balance at the bank or financial institution"
    "3. FinMoveMoney: Initiate money movement (transfer)",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to transfer some money",
            "agent: Sure! I can help you out with that. May I have account number and email address?",
            "user: my account number is 11235 and my email address is matt.murdock@nelsonmurdock.com",
            "user_confirmed_tool_run: <user clicks confirm on FincheckAccountIsValid tool>",
            "tool_result: { 'status': account valid }",
            "agent: Great! Here are your account balances:",
            "user_confirmed_tool_run: <user clicks confirm on FinCheckAccountBalance tool>",
            "tool_result: { 'name': Matt Murdock, 'email': matt.murdock@nelsonmurdock.com, 'account_id': 11235, 'checking_balance': 875.40, 'savings_balance': 3200.15, 'bitcoin_balance': 0.1378, 'account_creation_date': 2014-03-10 }",
            "agent: Your account balances are as follows: \\n "
            "Checking: $875.40. \\n "
            "Savings: $3200.15. \\n "
            "Bitcoint: 0.1378 \\n "
            "agent: how much would you like to move, from which account type, and to which account number?",
            "user: I'd like to move $500 from savings to account number #56789",
            "user_confirmed_tool_run: <user clicks confirm on FinMoveMoney tool>",
            "tool_result: { 'status': money movement complete, 'confirmation id': 333421, 'new_balance': $2700.15 }",
            "agent: Money movement completed! New account balance: $2700.15. Your confirmation id is 333421. ",
        ]
    ),
)

goal_fin_loan_application = AgentGoal(
    id="goal_fin_loan_application",
    category_tag="fin",
    agent_name="Easy Loan",
    agent_friendly_description="Initiate a simple loan application.",
    tools=[
        tool_registry.financial_check_account_is_valid,
        tool_registry.financial_submit_loan_approval,
    ],
    description="The user wants to apply for a loan at the financial institution. To assist with that goal, help the user gather args for these tools in order: "
    "1. FinCheckAccountIsValid: validate the user's account is valid"
    "2. FinCheckAccountSubmitLoanApproval: submit the loan for approval",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to apply for a loan",
            "agent: Sure! I can help you out with that. May I have account number and email address to validate your account?",
            "user: account number is 11235813",
            "user_confirmed_tool_run: <user clicks confirm on FincheckAccountIsValid tool>",
            "tool_result: { 'status': account valid }",
            "agent: Great! We've validated your account. What will the loan amount be?",
            "user: I'd like a loan for $500",
            "user_confirmed_tool_run: <user clicks confirm on FinCheckAccountSubmitLoanApproval tool>",
            "tool_result: { 'status': submitted, 'detailed_status': loan application is submitted and initial validation is complete, 'confirmation id': 333421, 'next_step': You'll receive a confirmation for final approval in three business days }",
            "agent: I have submitted your loan application process and the initial validation is successful. Your application ID is 333421. You'll receive a notification for final approval from us in three business days. ",
        ]
    ),
)

finance_goals: List[AgentGoal] = [
    goal_fin_check_account_balances,
    goal_fin_move_money,
    goal_fin_loan_application,
]
