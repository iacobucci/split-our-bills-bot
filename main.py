#!/bin/python3

import datetime

from telethon import TelegramClient, events, Button
from telethon.tl.functions.users import GetFullUserRequest
import telethon.tl.types as types
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Float, or_
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from sec import API_ID, API_HASH, BOT_TOKEN
from persistance import Expense, session

HALF_TABLE_LEN=20

def log(message):
	print(f"[{datetime.datetime.now()}] " + message)

def add_expense(paying_user: int, other_user:int, amount:float, description=None):
	[user_1, user_2] = sorted([paying_user, other_user])

	new_expense = Expense(
		user_1=user_1,
		user_2=user_2,
		paying_user=paying_user,
		amount=amount,
		description=description
	)
	session.add(new_expense)
	session.commit()

async def get_balance(user_requesting, other_user):
	[user_1, user_2] = sorted([user_requesting, other_user])
	user_1_name = await get_user_label(user_1)
	user_2_name = await get_user_label(user_2)

	expenses = session.query(Expense).filter(Expense.user_1 == user_1, Expense.user_2 == user_2).all()

	user_1_total = 0
	user_2_total = 0

	for expense in expenses:
		if expense.paying_user == user_1:
			user_1_total += expense.amount
		if expense.paying_user == user_2:
			user_2_total += expense.amount
	
	if user_1_total > user_2_total:
		balance = user_1_total - user_2_total
		return user_2_name + " owes " + user_1_name + " " + format_currency(balance)
	elif user_2_total > user_1_total:
		balance = user_2_total - user_1_total
		return user_1_name + " owes " + user_2_name + " " + format_currency(balance)
	else:
		balance = 0
		return "All square!"


def format_currency(amount):
	return "€{:.2f}".format(amount)

def adjust_line(line):
	if len(line) > HALF_TABLE_LEN - 2:
		return " " + line[:HALF_TABLE_LEN - 3] + "… "
	else:
		return " " + line + " " * (HALF_TABLE_LEN - len(line) - 1)

async def get_all_history(user_requesting, other_user):
	[user_1, user_2] = sorted([user_requesting, other_user])

	expenses = session.query(Expense).filter(Expense.user_1 == user_1, Expense.user_2 == user_2).all()

	summary = "```"

	user_1_expenses = []
	user_2_expenses = []

	for expense in expenses:
		description = expense.description
		amount = expense.amount

		if expense.paying_user == user_1:
			user_1_expenses.append(amount)

		if expense.paying_user == user_2:
			user_2_expenses.append(amount)

	summary += (adjust_line(await get_user_label(user_1))+"|"+adjust_line(await get_user_label(user_2))) + "\n"

	summary += ("-" * HALF_TABLE_LEN + "|" + "-" * HALF_TABLE_LEN) + "\n"

	for i in range(max(len(user_1_expenses), len(user_2_expenses))):
		if i < len(user_1_expenses):
			user_1_expense = format_currency(user_1_expenses[i])
		else:
			user_1_expense = ""
		if i < len(user_2_expenses):
			user_2_expense = format_currency(user_2_expenses[i])
		else:
			user_2_expense = ""
		summary += (adjust_line(user_1_expense)+"|"+adjust_line(user_2_expense)) + "\n"

	summary += "```"

	return summary

async def get_short_history(user_requesting, other_user):
	[user_1, user_2] = sorted([user_requesting, other_user])

	summary = "```"

	expenses_user_1 = (
		session.query(Expense)
		.filter(
			Expense.user_1 == user_1,
			Expense.user_2 == user_2,
			Expense.paying_user == user_1
		)
		.order_by(Expense.timestamp.desc())
		.limit(5)
		.all()
	)

	summary += await get_user_label(user_1) + ":\n"
	for expense in expenses_user_1:
		description = expense.description
		amount = expense.amount
		if description is None:
			summary += f"{format_currency(amount)}" + "\n"
		else:
			summary += f"{format_currency(amount)} ({description})" + "\n"
	summary += "\n"

	expenses_user_2 = (
		session.query(Expense)
		.filter(
			Expense.user_1 == user_1,
			Expense.user_2 == user_2,
			Expense.paying_user == user_2
		)
		.order_by(Expense.timestamp.desc())
		.limit(5)
		.all()
	)

	summary += await get_user_label(user_2) + ":\n"
	for expense in expenses_user_2:
		description = expense.description
		amount = expense.amount
		if description is None:
			summary += f"{format_currency(amount)}" + "\n"
		else:
			summary += f"{format_currency(amount)} ({description})" + "\n"

	summary += "```"
	return summary

def clear_database():
	session.query(Expense).delete()
	session.commit()

# Bot startup
bot = TelegramClient('bot', int(API_ID), API_HASH).start(bot_token=BOT_TOKEN)

async def get_user_label(user_id):
	global bot
	try:
		user = await bot.get_entity(user_id)
		# Check if user has an username
		username = user.username if user.username else ""
		
		# Check if user has a first and/or last name
		first_name = user.first_name if user.first_name else ""
		last_name = user.last_name if user.last_name else ""
		if first_name != "":
			full_name = first_name
			if last_name != "":
				full_name += " " + last_name
		else:
			full_name = ""

		if full_name != "":
			label = full_name
		else:
			if username != "":
				label = username
			else:
				label = f"User {user_id}"

		return label
	except Exception as e:
		log(f"Error getting user label: {e}")
		return None

def get_amount_and_description_from_query(query):
	amount = 0
	description = None
	words = query.split(" ")
	
	if len(words) > 0:
		try:
			amount = float(words[0])
		except ValueError:
			amount = 0

	if len(words) > 1:
		description = " ".join(words[1:])

	return amount, description

def expense_amount_and_description(amount,description):
	summary = format_currency(amount)
	if description:
		summary += f" for {description}"
	return summary

def get_all_accounts_the_user_is_involved_in(user_id):
	accounts = session.query(
		Expense.user_1,
		Expense.user_2
	).filter(
		or_(Expense.user_1 == user_id, Expense.user_2 == user_id)
	).group_by(
		Expense.user_1,
		Expense.user_2
	).all()
	return accounts

@bot.on(events.InlineQuery)
async def inline_handler(event):
	query = event.text # Extract the text from the query
	builder = event.builder
	user_id = event.sender_id
	sender = await event.get_sender()

	amount, description = get_amount_and_description_from_query(query)
	
	balance_articles = []

	for account in get_all_accounts_the_user_is_involved_in(user_id):
		other_user_id = account.user_1 if account.user_1 != user_id else account.user_2
		other_user_label = await get_user_label(other_user_id)

		balance = await get_balance(user_id, other_user_id) # the balance is gotten from the database

		balance_articles.append(
			builder.article(
				title=f"Balance with {other_user_label}",
				description=f"Click to see the balance with {other_user_label}",
				text=balance,
				thumb=None,
				buttons=[
					Button.inline("Show all history", data=f"all_history:::{user_id}:::{other_user_id}"),
					Button.inline("Show recent history", data=f"short_history:::{user_id}:::{other_user_id}")
				]
			)
		)
	
	if amount > 0:
		add_expense_article = builder.article(
			title="Add an expense",
			description=f"Click to add a WHOLE expense of {expense_amount_and_description(amount, description)}",
			text=f"Adding new expense of {expense_amount_and_description(amount, description)}",
			buttons=[
				Button.inline("Confirm", data=f"add_expense:::{amount}:::{user_id}:::{description}")
			]
		)

		add_split_expense_article = builder.article(
			title="Add an expense",
			description=f"Click to add a SPLIT expense of {expense_amount_and_description(amount, description)}",
			text=f"Adding new expense of {expense_amount_and_description(amount/2, description)}",
			buttons=[
				Button.inline("Confirm", data=f"add_expense:::{amount/2}:::{user_id}:::{description}")
			]
		)

		await event.answer([add_expense_article, add_split_expense_article] + balance_articles)
	else:
		await event.answer(balance_articles)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
	data = event.data.decode('utf-8')
	
	if data.startswith("add_expense:::"):
		# Estrai i dati dal callback
		_, amount, user_id, description = data.split(":::")
		amount = float(amount)
		# take just the first two decimals
		amount = round(amount, 2)

		user_id = int(user_id)
		other_user_id = event.sender_id

		if user_id == other_user_id:
			await event.edit("😤 You must let the other person confirm your expense, you greedy!")
			return

		add_expense(paying_user=user_id, other_user=other_user_id, amount=amount, description=description)

		# Qui inserisci la logica per aggiungere la spesa
		await event.edit(f"✅ Expense of {format_currency(amount)} added successfully!")
		
	elif data.startswith("all_history:::"):
		# Estrai l'user_id
		_, user_id, other_user_id = data.split(":::")
		user_id = int(user_id)
		other_user_id = int(other_user_id)

		balance = await get_balance(user_id, other_user_id)
		history = await get_all_history(user_id, other_user_id)

		summary = str(balance) + str(history)
		
		await event.edit(summary)

	elif data.startswith("short_history:::"):
		# Estrai l'user_id
		_, user_id, other_user_id = data.split(":::")
		user_id = int(user_id)
		other_user_id = int(other_user_id)

		balance = await get_balance(user_id, other_user_id)
		history = await get_short_history(user_id, other_user_id)

		summary = str(balance) + str(history)
		
		await event.edit(summary)


if __name__ == "__main__":
	log("Bot started!")
	bot.run_until_disconnected()
