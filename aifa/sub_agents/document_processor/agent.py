"""Document processor sub-agent."""

from google.adk.agents import LlmAgent

from aifa.tools.pdf_extractor import extract_pdf_fields
from . import prompt

MODEL = "gemini-2.0-flash"

document_processor_agent = LlmAgent(
    name="document_processor",
    model=MODEL,
    description=(
        "Extracts structured data fields from Malaysian insurance and takaful "
        "PDF documents (quotations, e-policies, cover notes, receipts, credit "
        "notes, endorsements) and returns a clean JSON summary."
    ),
    instruction=prompt.DOCUMENT_PROCESSOR_PROMPT,
    output_key="document_processor_output",
    tools=[extract_pdf_fields],
)
