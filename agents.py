import autogen
import os
from dotenv import load_dotenv
from database import save_agent_output, save_system_prompt

load_dotenv()

# Configuration for the LLM
config_list = [
    {
        "model": os.getenv("MODEL", "gpt-4o"),
        "api_key": os.getenv("AZURE_API_KEY"),
        "base_url": os.getenv("AZURE_API_BASE"),
        "api_type": "azure",
        "api_version": os.getenv("AZURE_API_VERSION"),
    }
]

llm_config = {
    "config_list": config_list,
    "temperature": 0.2,
}

# 1. Incident Analysis Agent
analyst_system_message = """
You are an Incident Analysis Agent. 
Your goal is to understand the incident clearly and restate it correctly.
Tasks:
1. Identify: What happened, When, Who was impacted.
2. Separate symptoms from the actual problem.
Output: A refined problem statement and key facts/assumptions.
Keep it structured and professional.
"""

# 2. Root Cause Identification Agent
identifier_system_message = """
You are a Root Cause Identification Agent.
Your goal is to identify likely root causes logically using People, Process, Tools/Systems, and External factors.
Tasks:
1. Generate 3–5 plausible root causes.
2. Explain how each caused the issue.
3. Distinguish between a root cause and a contributing factor.
Output: A structured list of root causes and contributing factors.
"""

# 3. Mitigation & Prevention Agent
mitigator_system_message = """
You are a Mitigation & Prevention Agent.
Your goal is to turn analysis into action.
Tasks:
1. Suggest Corrective actions (to fix the immediate issue).
2. Suggest Preventive actions (to avoid recurrence).
3. Prioritize actions by impact & effort.
Output: A prioritized action plan with clear owners and timelines (hypothetical).
"""

# 4. Critic / Validator Agent
validator_system_message = """
You are a Critic / Validator Agent.
Your goal is quality control.
Checks:
1. Are the identified causes actually root causes?
2. Are actions specific or vague?
3. Is the logic consistent end-to-end?
Behavior:
- If quality is high, output 'TERMINATE' and provide the Final RCA Report.
- If not, request a specific revision from the relevant agent.
"""

def get_agents(session_id, progress_cb=None):
    user_proxy = autogen.UserProxyAgent(
        name="User_Proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
        code_execution_config=False,
    )

    analyst = autogen.AssistantAgent(
        name="Incident_Analyst",
        system_message=analyst_system_message,
        llm_config=llm_config,
    )

    identifier = autogen.AssistantAgent(
        name="Root_Cause_Identifier",
        system_message=identifier_system_message,
        llm_config=llm_config,
    )

    mitigator = autogen.AssistantAgent(
        name="Mitigation_Agent",
        system_message=mitigator_system_message,
        llm_config=llm_config,
    )

    validator = autogen.AssistantAgent(
        name="Validator_Agent",
        system_message=validator_system_message,
        llm_config=llm_config,
    )

    # Save prompts to DB
    save_system_prompt("Incident_Analyst", analyst_system_message)
    save_system_prompt("Root_Cause_Identifier", identifier_system_message)
    save_system_prompt("Mitigation_Agent", mitigator_system_message)
    save_system_prompt("Validator_Agent", validator_system_message)

    # Registering hooks to save outputs to DB
    def save_output(sender, message, recipient, silent):
        content = message.get("content", "") if isinstance(message, dict) else str(message)
        if content and sender.name != "User_Proxy":
            save_agent_output(session_id, sender.name, content)
            if progress_cb:
                progress_cb(sender.name)
        return message

    # Attach the hook to agents (except UserProxy)
    for agent in [analyst, identifier, mitigator, validator]:
        agent.register_hook(hookable_method="process_message_before_send", hook=save_output)

    return user_proxy, [analyst, identifier, mitigator, validator]

def run_rca_workflow(incident_desc, session_id, progress_cb=None):
    user_proxy, agents = get_agents(session_id, progress_cb)
    
    groupchat = autogen.GroupChat(
        agents=[user_proxy] + agents,
        messages=[],
        max_round=12,
        speaker_selection_method="round_robin"
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    
    user_proxy.initiate_chat(
        manager,
        message=f"Please perform a complete Root Cause Analysis for this incident: {incident_desc}"
    )
    
    return groupchat.messages
