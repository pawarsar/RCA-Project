-- schema.sql
-- Optimized for Vercel Postgres

BEGIN;

-- 1. Create Schema
CREATE SCHEMA IF NOT EXISTS rca_db;

-- 2. Set Search Path
SET search_path TO rca_db, public;

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

-- 8. Indices for Performance
CREATE INDEX IF NOT EXISTS idx_agent_outputs_session_id ON rca_db.agent_outputs(session_id);
CREATE INDEX IF NOT EXISTS idx_final_reports_session_id ON rca_db.final_reports(session_id);

COMMIT;
