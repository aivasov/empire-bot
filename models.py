import os
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	telegram_id = Column(String, unique=True, index=True, nullable=False)
	state = Column(String, default='0_0')  # формат "blockIndex_questionIndex"
	total_score = Column(Integer, default=0)

# Инициализация БД
DB_PATH = os.getenv('DATABASE_URL', 'sqlite:///quiz.db')
engine = create_engine(DB_PATH, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)
