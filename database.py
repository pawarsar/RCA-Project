import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use DATABASE_URL or POSTGRES_URL for deployment (e.g., Vercel, Heroku)
# Fallback to a default local connection if not found
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    # Local Development Fallback
    # DATABASE_URL = "postgresql://postgres:pawar06@localhost:5432/postgres"
    raise ValueError("DATABASE_URL environment variable is not set. Please provide a PostgreSQL connection string in your .env file.")

# For Vercel Postgres, we might need to handle sslmode
if DATABASE_URL and "vercel-storage.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-csearch_path=rca_db,public"} if DATABASE_URL and "rca_db" in DATABASE_URL else {}
)

# if not DB_URL:
#     raise ValueError("DATABASE_URL environment variable is not set. Please provide a PostgreSQL connection string in your .env file.")

# engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AgentOutput(Base):
    __tablename__ = "agent_outputs"
    __table_args__ = {"schema": "rca_db"}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    agent_name = Column(String(100))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SystemPrompt(Base):
    __tablename__ = "system_prompts"
    __table_args__ = {"schema": "rca_db"}

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), unique=True)
    prompt_text = Column(Text)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class FinalReport(Base):
    __tablename__ = "final_reports"
    __table_args__ = {"schema": "rca_db"}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, unique=True)
    incident_description = Column(Text)
    final_report = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_agent_output(session_id, agent_name, content):
    db = SessionLocal()
    try:
        new_output = AgentOutput(
            session_id=session_id,
            agent_name=agent_name,
            content=content
        )
        db.add(new_output)
        db.commit()
    finally:
        db.close()

def save_system_prompt(agent_name, prompt_text):
    db = SessionLocal()
    try:
        # Check if exists, update if so
        existing = db.query(SystemPrompt).filter(SystemPrompt.agent_name == agent_name).first()
        if existing:
            existing.prompt_text = prompt_text
        else:
            new_prompt = SystemPrompt(agent_name=agent_name, prompt_text=prompt_text)
            db.add(new_prompt)
        db.commit()
    finally:
        db.close()

def save_final_report(session_id, incident_description, final_report):
    db = SessionLocal()
    try:
        report = FinalReport(
            session_id=session_id,
            incident_description=incident_description,
            final_report=final_report
        )
        db.add(report)
        db.commit()
    finally:
        db.close()
