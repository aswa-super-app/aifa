"""Policy adviser sub-agent."""

from google.adk.agents import LlmAgent

from . import prompt

MODEL = "gemini-2.0-flash"

policy_advisor_agent = LlmAgent(
    name="policy_advisor",
    model=MODEL,
    description=(
        "Recommends the most suitable takaful/insurance quotation for a client "
        "based on their profile and the RFQ Analyser's structured comparison. "
        "Provides next steps for policy purchase and reminds users that advice "
        "is for informational purposes only."
    ),
    instruction=prompt.POLICY_ADVISOR_PROMPT,
    output_key="policy_advisor_output",
)
