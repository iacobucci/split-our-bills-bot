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
	amount = Column(Integer, nullable=False)
	description = Column(String, nullable=True)
	timestamp = Column(DateTime, default=func.now())

Base.metadata.create_all(engine)