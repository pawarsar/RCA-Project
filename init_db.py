import psycopg2
import os
from psycopg2 import sql
from dotenv import load_dotenv
from agents import analyst_system_message, identifier_system_message, mitigator_system_message, validator_system_message

load_dotenv()

# Parse DATABASE_URL for psycopg2 connection
# Expected format: postgresql://user:password@host:port/dbname
# db_url = os.getenv("DATABASE_URL")
# Update these connection parameters as needed
DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': os.getenv("POSTGRES_HOST"),
    'port': os.getenv("POSTGRES_PORT")
}

# SQL Script for RCA Intelligence Engine
SQL_SCRIPT = """
-- RCA Assistant database objects
-- Target DB: PostgreSQL

CREATE SCHEMA IF NOT EXISTS rca_db;

SET search_path TO rca_db;

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS agent_outputs (
    id              SERIAL PRIMARY KEY,
    session_id      VARCHAR(100),
    agent_name      VARCHAR(100),
    content         TEXT,
    timestamp       TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS system_prompts (
    id              SERIAL PRIMARY KEY,
    agent_name      VARCHAR(100) UNIQUE,
    prompt_text     TEXT,
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS final_reports (
    id                      SERIAL PRIMARY KEY,
    session_id              VARCHAR(100) UNIQUE,
    incident_description    TEXT,
    final_report            TEXT,
    timestamp               TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_agent_outputs_session_id ON agent_outputs(session_id);
CREATE INDEX IF NOT EXISTS ix_final_reports_session_id ON final_reports(session_id);
"""

def run_db_initialization():
    conn = None
    try:
        print(f"🔗 Connecting to PostgreSQL...")
        # conn = psycopg2.connect(db_url)
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        
        with conn.cursor() as cur:
            # 1. Execute Table Creation Script
            print("🏗️ Creating tables...")
            cur.execute(SQL_SCRIPT)
            
            # 2. Store/Update Prompts in system_prompts table
            print("📝 Seeding agent prompts...")
            prompts = [
                ("Incident_Analyst", analyst_system_message),
                ("Root_Cause_Identifier", identifier_system_message),
                ("Mitigation_Agent", mitigator_system_message),
                ("Validator_Agent", validator_system_message)
            ]
            
            for agent_name, prompt_text in prompts:
                upsert_query = """
                INSERT INTO system_prompts (agent_name, prompt_text, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (agent_name) 
                DO UPDATE SET prompt_text = EXCLUDED.prompt_text, updated_at = now();
                """
                cur.execute(upsert_query, (agent_name, prompt_text))
            
            conn.commit()
            print("✅ Database initialized and prompts seeded successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if not DB_CONFIG:
        print("❌ Error: Database configuration not found in .env file.")
    else:
        run_db_initialization()
