"""Root agent for AIFA — AI Financial Adviser.

This module exposes ``root_agent`` which is the entry-point required by the
Google Agent Development Kit (ADK) CLI (``adk web`` / ``adk run``).
"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.document_processor import document_processor_agent
from .sub_agents.policy_advisor import policy_advisor_agent
from .sub_agents.rfq_analyzer import rfq_analyzer_agent

MODEL = "gemini-2.0-flash"

aifa_coordinator = LlmAgent(
    name="aifa_coordinator",
    model=MODEL,
    description=(
        "AIFA coordinator — guides users through takaful/insurance quotation "
        "requests, PDF document data extraction, multi-quote comparison, and "
        "policy recommendations for ASWA Advisory Sdn Bhd."
    ),
    instruction=prompt.AIFA_COORDINATOR_PROMPT,
    output_key="aifa_coordinator_output",
    tools=[
        AgentTool(agent=document_processor_agent),
        AgentTool(agent=rfq_analyzer_agent),
        AgentTool(agent=policy_advisor_agent),
    ],
)

root_agent = aifa_coordinator
