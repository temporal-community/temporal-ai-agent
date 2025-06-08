from typing import List

import tools.tool_registry as tool_registry
from models.tool_definitions import AgentGoal

starter_prompt_generic = (
    "Welcome me, give me a description of what you can do, then ask me for the details you need to do your job."
)

goal_hr_schedule_pto = AgentGoal(
    id="goal_hr_schedule_pto",
    category_tag="hr",
    agent_name="Schedule PTO",
    agent_friendly_description="Schedule PTO based on your available PTO.",
    tools=[
        tool_registry.current_pto_tool,
        tool_registry.future_pto_calc_tool,
        tool_registry.book_pto_tool,
    ],
    description="The user wants to schedule paid time off (PTO) after today's date. To assist with that goal, help the user gather args for these tools in order: "
    "1. CurrentPTO: Tell the user how much PTO they currently have "
    "2. FuturePTOCalc: Tell the user how much PTO they will have as of the prospective future date "
    "3. BookPTO: Book PTO after user types 'yes'",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to schedule some time off",
            "agent: Sure! Let's start by determining how much PTO you currently have. May I have your email address?",
            "user: bob.johnson@emailzzz.com",
            "agent: Great! I can tell you how much PTO you currently have accrued.",
            "user_confirmed_tool_run: <user clicks confirm on CurrentPTO tool>",
            "tool_result: { 'num_hours': 400, 'num_days': 50 }",
            "agent: You have 400 hours, or 50 days, of PTO available. What dates would you like to take your time off? ",
            "user: Dec 1 through Dec 5",
            "agent: Let's check if you'll have enough PTO accrued by Dec 1 of this year to accomodate that.",
            "user_confirmed_tool_run: <user clicks confirm on FuturePTO tool>"
            'tool_result: {"enough_pto": True, "pto_hrs_remaining_after": 410}',
            "agent: You do in fact have enough PTO to accommodate that, and will have 410 hours remaining after you come back. Do you want to book the PTO? ",
            "user: yes ",
            "user_confirmed_tool_run: <user clicks confirm on BookPTO tool>",
            'tool_result: { "status": "success" }',
            "agent: PTO successfully booked! ",
        ]
    ),
)

goal_hr_check_pto = AgentGoal(
    id="goal_hr_check_pto",
    category_tag="hr",
    agent_name="Check PTO Amount",
    agent_friendly_description="Check your available PTO.",
    tools=[
        tool_registry.current_pto_tool,
    ],
    description="The user wants to check their paid time off (PTO) after today's date. To assist with that goal, help the user gather args for these tools in order: "
    "1. CurrentPTO: Tell the user how much PTO they currently have ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to check my time off amounts at the current time",
            "agent: Sure! I can help you out with that. May I have your email address?",
            "user: bob.johnson@emailzzz.com",
            "agent: Great! I can tell you how much PTO you currently have accrued.",
            "user_confirmed_tool_run: <user clicks confirm on CurrentPTO tool>",
            "tool_result: { 'num_hours': 400, 'num_days': 50 }",
            "agent: You have 400 hours, or 50 days, of PTO available.",
        ]
    ),
)

goal_hr_check_paycheck_bank_integration_status = AgentGoal(
    id="goal_hr_check_paycheck_bank_integration_status",
    category_tag="hr",
    agent_name="Check paycheck deposit status",
    agent_friendly_description="Check your integration between your employer and your financial institution.",
    tools=[
        tool_registry.paycheck_bank_integration_status_check,
    ],
    description="The user wants to check their bank integration used to deposit their paycheck. To assist with that goal, help the user gather args for these tools in order: "
    "1. CheckPayBankStatus: Tell the user the status of their paycheck bank integration ",
    starter_prompt=starter_prompt_generic,
    example_conversation_history="\n ".join(
        [
            "user: I'd like to check paycheck bank integration",
            "agent: Sure! I can help you out with that. May I have your email address?",
            "user: bob.johnson@emailzzz.com",
            "agent: Great! I can tell you what the status is for your paycheck bank integration.",
            "user_confirmed_tool_run: <user clicks confirm on CheckPayBankStatus tool>",
            "tool_result: { 'status': connected }",
            "agent: Your paycheck bank deposit integration is properly connected.",
        ]
    ),
)

hr_goals: List[AgentGoal] = [
    goal_hr_schedule_pto,
    goal_hr_check_pto,
    goal_hr_check_paycheck_bank_integration_status,
]