import importlib
import json
import shutil
from pathlib import Path

import pytest

import tools.tool_registry as tool_registry

move_money_module = importlib.import_module("tools.fin.move_money")

REPO_DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "tools"
    / "data"
    / "customer_account_data.json"
)
EMAIL = "matt.murdock@nelsonmurdock.com"
ACCOUNT_ID = "11235"


@pytest.fixture
def data_file(tmp_path, monkeypatch):
    """Point move_money at a tmp copy of the mock data; never start a workflow."""
    (tmp_path / "data").mkdir()
    (tmp_path / "fin").mkdir()
    copy = tmp_path / "data" / "customer_account_data.json"
    shutil.copyfile(REPO_DATA_FILE, copy)
    # move_money builds its data path from its module __file__
    monkeypatch.setattr(
        move_money_module, "__file__", str(tmp_path / "fin" / "move_money.py")
    )
    monkeypatch.setenv("FIN_START_REAL_WORKFLOW", "false")
    return copy


def _args(account_key: str) -> dict:
    return {
        "email_address_or_account_ID": account_key,
        "accounttype": "checking",
        "amount": "100",
        "destinationaccount": "savings",
        "userConfirmation": "yes",
    }


def _arg(tool, name):
    return next(a for a in tool.arguments if a.name == name)


@pytest.mark.asyncio
@pytest.mark.parametrize("account_key", [EMAIL, ACCOUNT_ID])
async def test_move_money_one_identifier_succeeds(data_file, account_key):
    result = await move_money_module.move_money(_args(account_key))

    assert result["status"] == "money movement complete"
    account = next(
        a for a in json.loads(data_file.read_text())["accounts"] if a["email"] == EMAIL
    )
    assert result["new_balance"] == account["checking_balance"]


@pytest.mark.asyncio
async def test_move_money_joined_identifiers_not_found(data_file):
    before = data_file.read_text()

    result = await move_money_module.move_money(_args(f"{EMAIL}, {ACCOUNT_ID}"))

    assert "error" in result
    assert "Account not found" in result["error"]
    assert data_file.read_text() == before


def test_move_money_account_arg_asks_for_one_value():
    desc = _arg(
        tool_registry.financial_move_money, "email_address_or_account_ID"
    ).description.lower()

    assert "need both" not in desc
    assert "exactly one" in desc
    assert "email" in desc and "account id" in desc


def test_move_money_amount_arg_is_a_dollar_amount():
    desc = _arg(tool_registry.financial_move_money, "amount").description.lower()

    assert "checking" not in desc and "savings" not in desc
    assert "dollar" in desc
