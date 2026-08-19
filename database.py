from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
import uuid

# 1. The Engine Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat_history.db"

# check_same_thread=False is required for SQLite and FastAPI to play nicely together
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 2. The Session Manager
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. The Base Model
Base = declarative_base()

# 4. Our Two Minimal Tables
class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)  # Will store 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())