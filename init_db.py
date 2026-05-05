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
-- schema.sql
-- Optimized for Vercel Postgres

BEGIN;

-- 1. Create Schema
CREATE SCHEMA IF NOT EXISTS rca_db;

-- 2. Set Search Path
SET search_path TO rca_db;

-- 3. Extensions (Optional)
CREATE EXTENSION IF NOT EXISTS postgis;

-- 4. Table for Users
CREATE TABLE IF NOT EXISTS rca_db.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Table for Agent Outputs
CREATE TABLE IF NOT EXISTS rca_db.agent_outputs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    agent_name VARCHAR(100),
    content TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Table for System Prompts
CREATE TABLE IF NOT EXISTS rca_db.system_prompts (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) UNIQUE,
    prompt_text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Table for Final Reports
CREATE TABLE IF NOT EXISTS rca_db.final_reports (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE,
    user_id INTEGER REFERENCES rca_db.users(id),
    incident_description TEXT,
    final_report TEXT,
    root_cause_category VARCHAR(100),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    total_tokens INTEGER DEFAULT 0,
    estimated_cost NUMERIC(10, 6) DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --- MIGRATION LOGIC FOR EXISTING TABLES ---
DO $$ 
BEGIN 
    -- Add user_id if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='rca_db' AND table_name='final_reports' AND column_name='user_id') THEN
        ALTER TABLE rca_db.final_reports ADD COLUMN user_id INTEGER REFERENCES rca_db.users(id);
    END IF;
    
    -- Add total_tokens if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='rca_db' AND table_name='final_reports' AND column_name='total_tokens') THEN
        ALTER TABLE rca_db.final_reports ADD COLUMN total_tokens INTEGER DEFAULT 0;
    END IF;
    
    -- Add estimated_cost if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='rca_db' AND table_name='final_reports' AND column_name='estimated_cost') THEN
        ALTER TABLE rca_db.final_reports ADD COLUMN estimated_cost NUMERIC(10, 6) DEFAULT 0;
    END IF;
END $$;

-- 8. Indices for Performance
CREATE INDEX IF NOT EXISTS idx_agent_outputs_session_id ON rca_db.agent_outputs(session_id);
CREATE INDEX IF NOT EXISTS idx_final_reports_session_id ON rca_db.final_reports(session_id);

COMMIT;
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
