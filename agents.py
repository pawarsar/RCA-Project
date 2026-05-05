import autogen
import os
from dotenv import load_dotenv
from database import save_agent_output, save_system_prompt
from duckduckgo_search import DDGS
import json

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
You are an expert Incident Analysis Agent. 
Your goal is to parse incident reports and extract the technical essence without fluff.

**STRICT OUTPUT FORMAT**:
1. **Actual Problem**: A single, precise sentence describing the core failure.
2. **Symptoms**: A bulleted list of observed behaviors that led to the discovery.
3. **Timeline**: Key timestamps (if available).

Behavior: Be direct. Do not add introductory sentences like "Based on my analysis...".
"""

# 2. Root Cause Identification Agent
identifier_system_message = """
You are a Senior Root Cause Identification Agent. 
Your goal is to identify the **DEEP** technical and process-level root causes.

**Guidelines**:
- Focus strictly on "Confirmed Root Causes".
- Avoid generic causes like "human error" unless explained by a process failure.
- Use the **5-Whys** approach internally but only output the final, confirmed findings.

**STRICT OUTPUT FORMAT**:
- **Confirmed Root Causes**: A structured list explaining the "Why" behind the "How".
- **Contributing Factors**: Secondary issues that exacerbated the incident.

Keep it clinical and precise. No fluff.
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
You are the Lead RCA Validator. 
Your goal is to synthesize the final report into a masterpiece of precision.

**Report Requirements**:
1. **Title**: Professional incident name.
2. **Executive Summary**: 2-3 sentences max.
3. **Actual Problem vs Symptoms**: Clearly defined.
4. **Confirmed Root Causes**: The core findings.
5. **Action Plan**: Immediate and Long-term.
6. **Mermaid Diagram**: Visual representation.

**STRICT INSTRUCTION**: 
Remove all conversational filler. No "Great work everyone", no "I agree with...". 
The final output must be a professional document ready for C-level review.

**MANDATORY**: Include a Mermaid.js diagram in your final report.
```mermaid
graph TD
    A[Incident] --> B[Root Cause]
    B --> C[Action Item]
```

Output the report and end with 'TERMINATE'.
"""

def search_tool(query: str) -> str:
    """Search the web for information using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return json.dumps(results)
    except Exception as e:
        return f"Search failed: {str(e)}"

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
    
    # Register tools for the Identifier agent
    autogen.agentchat.register_function(
        search_tool,
        caller=agents[1], # Root_Cause_Identifier
        executor=user_proxy,
        name="web_search",
        description="Search the web for incident context or root cause information."
    )
    
    groupchat = autogen.GroupChat(
        agents=[user_proxy] + agents,
        messages=[],
        max_round=12,
        speaker_selection_method="round_robin"
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    
    chat_res = user_proxy.initiate_chat(
        manager,
        message=f"Please perform a complete Root Cause Analysis for this incident: {incident_desc}"
    )
    
    # Extract token usage and cost from ALL agents in the group chat
    total_tokens = 0
    total_cost = 0.0
    
    for agent in [user_proxy] + agents:
        if hasattr(agent, 'client_cache') and agent.client_cache:
            # Note: Some versions use different internal structures for usage
            pass 
        
        # Most reliable way in modern AutoGen:
        if hasattr(agent, 'previous_usage_summary') and agent.previous_usage_summary:
            total_tokens += agent.previous_usage_summary.get('total_tokens', 0)
            total_cost += agent.previous_usage_summary.get('total_cost', 0.0)
            
    # If the summary is empty, check the chat_res as a fallback
    if total_tokens == 0:
        if hasattr(chat_res, 'cost'):
            total_cost = chat_res.cost.get('total_cost', 0.0)
        if hasattr(chat_res, 'usage'):
            total_tokens = chat_res.usage.get('total_tokens', 0)
        
    return groupchat.messages, total_tokens, total_cost
