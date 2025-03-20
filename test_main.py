import pytest

from main import get_amount_and_description_from_query

def test_get_amount_and_description_from_query():
	query = "10.50 pizza"
	assert get_amount_and_description_from_query(query) == (10.5, "pizza")
	query = "10.50"
	assert get_amount_and_description_from_query(query) == (10.5, None)
	query = "pizza"
	assert get_amount_and_description_from_query(query) == (0, None)