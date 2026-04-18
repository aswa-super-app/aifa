"""RFQ analyser sub-agent."""

from google.adk.agents import LlmAgent

from . import prompt

MODEL = "gemini-2.0-flash"

rfq_analyzer_agent = LlmAgent(
    name="rfq_analyzer",
    model=MODEL,
    description=(
        "Analyses one or more extracted insurance/takaful quotation records, "
        "summarises each quote, builds a side-by-side comparison table when "
        "multiple quotes are present, and highlights key observations such as "
        "price differences and coverage gaps."
    ),
    instruction=prompt.RFQ_ANALYZER_PROMPT,
    output_key="rfq_analyzer_output",
)
