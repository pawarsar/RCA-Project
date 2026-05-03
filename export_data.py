import json
import os
from sqlalchemy.orm import Session
from database import SessionLocal, AgentOutput, FinalReport, SystemPrompt

def export_to_json():
    db = SessionLocal()
    try:
        # Fetch Agent Outputs
        agent_outputs = db.query(AgentOutput).all()
        agent_data = [
            {
                "id": o.id,
                "session_id": o.session_id,
                "agent_name": o.agent_name,
                "content": o.content,
                "timestamp": o.timestamp.isoformat()
            }
            for o in agent_outputs
        ]

        # Fetch Final Reports
        final_reports = db.query(FinalReport).all()
        report_data = [
            {
                "id": r.id,
                "session_id": r.session_id,
                "incident_description": r.incident_description,
                "final_report": r.final_report,
                "timestamp": r.timestamp.isoformat()
            }
            for r in final_reports
        ]

        # Fetch System Prompts
        system_prompts = db.query(SystemPrompt).all()
        prompt_data = [
            {
                "id": p.id,
                "agent_name": p.agent_name,
                "prompt_text": p.prompt_text,
                "updated_at": p.updated_at.isoformat()
            }
            for p in system_prompts
        ]

        export_payload = {
            "agent_outputs": agent_data,
            "final_reports": report_data,
            "system_prompts": prompt_data
        }

        with open("rca_data_export.json", "w") as f:
            json.dump(export_payload, f, indent=4)
        
        print(f"Successfully exported {len(agent_data)} agent outputs, {len(report_data)} final reports, and {len(prompt_data)} prompts to rca_data_export.json")

    except Exception as e:
        print(f"Error during export: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting data export to JSON...")
    export_to_json()
