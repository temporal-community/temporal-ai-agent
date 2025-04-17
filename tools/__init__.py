from .search_fixtures import search_fixtures
from .search_flights import search_flights
from .search_trains import search_trains
from .search_trains import book_trains
from .create_invoice import create_invoice
from .find_events import find_events
from .list_agents import list_agents
from .change_goal import change_goal
from .transfer_control import transfer_control

from .hr.current_pto import current_pto
from .hr.book_pto import book_pto
from .hr.future_pto_calc import future_pto_calc
from .hr.checkpaybankstatus import checkpaybankstatus

from .fin.check_account_valid import check_account_valid
from .fin.get_account_balances import get_account_balance
from .fin.move_money import move_money
from .fin.submit_loan_application import submit_loan_application

from .ecommerce.get_order import get_order
from .ecommerce.track_package import track_package
from .ecommerce.list_orders import list_orders

from .give_hint import give_hint
from .guess_location import guess_location


def get_handler(tool_name: str):
    if tool_name == "SearchFixtures":
        return search_fixtures
    if tool_name == "SearchFlights":
        return search_flights
    if tool_name == "SearchTrains":
        return search_trains
    if tool_name == "BookTrains":
        return book_trains
    if tool_name == "CreateInvoice":
        return create_invoice
    if tool_name == "FindEvents":
        return find_events
    if tool_name == "ListAgents":
        return list_agents
    if tool_name == "ChangeGoal":
        return change_goal
    if tool_name == "TransferControl":
        return transfer_control
    if tool_name == "CurrentPTO":
        return current_pto
    if tool_name == "BookPTO":
        return book_pto
    if tool_name == "FuturePTOCalc":
        return future_pto_calc
    if tool_name == "CheckPayBankStatus":
        return checkpaybankstatus
    if tool_name == "FinCheckAccountIsValid":
        return check_account_valid
    if tool_name == "FinCheckAccountBalance":
        return get_account_balance    
    if tool_name == "FinMoveMoneyOrder":
        return move_money
    if tool_name == "FinCheckAccountSubmitLoanApproval":
        return submit_loan_application    
    if tool_name == "GetOrder":
        return get_order
    if tool_name == "TrackPackage":
        return track_package
    if tool_name == "ListOrders":
        return list_orders     
    if tool_name == "GiveHint":
        return give_hint
    if tool_name == "GuessLocation":
        return guess_location

    raise ValueError(f"Unknown tool: {tool_name}")
