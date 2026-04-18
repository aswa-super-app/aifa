# AIFA — AI Financial Adviser

AIFA is an AI-powered insurance and takaful advisory chatbot for
**ASWA Advisory Sdn Bhd**, built on the
[Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

It assists advisers and clients to:

- **Extract** structured data from Malaysian insurance/takaful PDF documents
  (quotations, e-policies, cover notes, receipts, credit notes).
- **Compare** multiple quotations side-by-side for the same risk.
- **Recommend** the most suitable policy based on client needs and budget.

> ⚠️ **Disclaimer**: AIFA is for educational and informational purposes only.
> It does not constitute binding financial or insurance advice.

---

## Architecture

AIFA is implemented as a multi-agent system following the ADK pattern:

```
aifa_coordinator          ← root LlmAgent (Gemini 2.0 Flash)
├── document_processor    ← extracts fields from PDF files
├── rfq_analyzer          ← compares & summarises quotations
└── policy_advisor        ← recommends best policy for client
```

### Package layout

```
aifa/
  __init__.py             re-exports root_agent for ADK CLI
  agent.py                root coordinator (aifa_coordinator)
  prompt.py               coordinator system prompt
  sub_agents/
    document_processor/   PDF field extraction agent
    rfq_analyzer/         quotation comparison agent
    policy_advisor/       policy recommendation agent
  tools/
    pdf_extractor.py      DocumentExtractor class + ADK tool functions
    data_cleaner.py       name / address / amount normalisation utilities
pyproject.toml
.env.example
```

---

## Prerequisites

- Python 3.11+
- [Google ADK](https://google.github.io/adk-docs/get-started) installed
- A Google AI API key **or** a Google Cloud project with Vertex AI enabled

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/aswa-super-app/aswaadvisory-aifa.git
cd aswaadvisory-aifa

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Configure environment variables
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY (and optionally GOOGLE_CLOUD_PROJECT)
```

---

## Running the agent

### Interactive web UI

```bash
adk web
```

Open the URL printed in the terminal, select **`aifa`** from the top-left
drop-down, and start chatting.

### Command-line

```bash
adk run aifa
```

---

## Example interactions

```
User: Hello, I am an adviser.

AIFA: Welcome! As an ASWA Advisory adviser, I can help you extract data from
      insurance PDFs, compare quotations, and recommend the best policy for
      your client. Please provide your name and email to get started.

User: My name is Ahmad, ahmad@aswa.com.my. I have a motor quotation PDF to
      process.

AIFA: Great, Ahmad! Please share the full file path to the PDF quotation so I
      can extract the details.

User: /home/ahmad/quotes/QUO_ETIQA_VDX1415.pdf

AIFA: [Calls document_processor → extract_pdf_fields]

      Here is what I extracted:
      - Document Type  : Quotation
      - Insurance Co.  : ETIQA GENERAL TAKAFUL BERHAD
      - Policy Number  : Q-2025-001234
      - Insured Name   : SEDAFIAT SDN BHD
      - Vehicle Reg    : VDX1415
      - Sum Covered    : RM 85,000.00
      - Total Payable  : RM 1,234.56
      - Coverage Period: 01/11/2025 – 31/10/2026

      Do you have additional quotes for the same vehicle to compare?
```

---

## Running tests

```bash
pytest
```

---

## Contributing

Please open a GitHub Issue or Pull Request. Ensure all new code includes
appropriate tests and follows the existing code style.
