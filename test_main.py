import datetime
import pytest

from main import (
	get_amount_and_description_from_query,
	calculate_balance_text,
	format_history_expense,
)
from persistance import Expense

def test_get_amount_and_description_from_query():
	query = "10.50 pizza"
	assert get_amount_and_description_from_query(query) == (10.5, "pizza")
	query = "10.50"
	assert get_amount_and_description_from_query(query) == (10.5, None)
	query = "pizza"
	assert get_amount_and_description_from_query(query) == (0, None)

def test_calculate_balance_text():
	# Test exact case from user request: Aurélie should cover next €19.09 SPLIT or €9.55 WHOLE
	text = calculate_balance_text("Valerio", "Aurélie", 626.0, 606.91)
	assert text == "Aurélie should cover the next €19.09 of SPLIT expenses or €9.55 of WHOLE expenses"

	# Test reverse debtor
	text = calculate_balance_text("Valerio", "Aurélie", 600.0, 610.50)
	assert text == "Valerio should cover the next €10.50 of SPLIT expenses or €5.25 of WHOLE expenses"

	# Test all square
	text = calculate_balance_text("Valerio", "Aurélie", 500.0, 500.0)
	assert text == "All square!"

def test_format_history_expense():
	dt = datetime.datetime(2026, 10, 19, 12, 0)

	exp_split = Expense(
		user_1=1,
		user_2=2,
		paying_user=1,
		amount=19.09,
		description="groceries",
		timestamp=dt,
		expense_type="SPLIT"
	)
	assert format_history_expense(exp_split) == "€19.09 (groceries) [SPLIT] [2026/10/19]"

	exp_whole = Expense(
		user_1=1,
		user_2=2,
		paying_user=2,
		amount=9.55,
		description=None,
		timestamp=dt,
		expense_type="WHOLE"
	)
	assert format_history_expense(exp_whole) == "€9.55 [WHOLE] [2026/10/19]"

	# Check description as string "None" (historical artifact in DB)
	exp_none_str = Expense(
		user_1=1,
		user_2=2,
		paying_user=2,
		amount=10.70,
		description="None",
		timestamp=dt,
		expense_type="WHOLE"
	)
	assert format_history_expense(exp_none_str) == "€10.70 [WHOLE] [2026/10/18]".replace("2026/10/18", "2026/10/19")

	# Check backwards compatibility with old records where expense_type is None
	exp_legacy = Expense(
		user_1=1,
		user_2=2,
		paying_user=1,
		amount=35.58,
		description="big groceries",
		timestamp=dt,
		expense_type=None
	)
	assert format_history_expense(exp_legacy) == "€35.58 (big groceries) [2026/10/19]"