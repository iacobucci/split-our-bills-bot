from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

engine = create_engine("sqlite:///database.db", poolclass=NullPool)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Expense(Base):
	__tablename__ = 'expenses'
	id = Column(Integer, primary_key=True, autoincrement=True)
	user_1 = Column(Integer, nullable=False) # user_1 is the user with the lowest id
	user_2 = Column(Integer, nullable=False) # user_2 is the user with the highest id
	paying_user = Column(Integer, nullable=False)
	amount = Column(Float, nullable=False)
	description = Column(String, nullable=True)
	timestamp = Column(DateTime, default=func.now())
	expense_type = Column(String, nullable=True)

Base.metadata.create_all(engine)

# Migration: ensure expense_type column exists in existing database
with engine.connect() as conn:
	columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(expenses)").fetchall()]
	if "expense_type" not in columns:
		conn.exec_driver_sql("ALTER TABLE expenses ADD COLUMN expense_type VARCHAR")
		conn.commit()