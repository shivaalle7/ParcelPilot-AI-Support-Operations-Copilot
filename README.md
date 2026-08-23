# ParcelPilot AI Support & Operations Copilot

A reliability-first AI support and operations copilot for the ParcelPilot assessment.

## What it implements

- Customer and internal support modes
- LangGraph-style tool orchestration
- Hybrid document retrieval: semantic + BM25
- Source authority / freshness / customer-agreement precedence
- Structured account/order/ticket lookup from the supplied Excel workbook
- Deterministic delay/SLA calculations
- Human confirmation before state-changing actions
- Code-enforced account-level authorization
- Proactive issue detection dashboard
- Evidence and confidence display
- Optional Groq LLM; deterministic fallback when no API key is present

## Important assessment-data note

The official six PDFs and `ParcelPilot_Assessment_Data.xlsx` were not available in the working files when this project was generated. Put them in:

`data/documents/`

The workbook should be placed at:

`data/ParcelPilot_Assessment_Data.xlsx`

The application discovers the files dynamically; it does not hard-code the example order IDs or answers.

Expected PDF files:
1. 01_Support_Policy_v3_CURRENT.pdf
2. 02_Support_Policy_v2_DEPRECATED.pdf
3. 03_Cancellation_and_Service_Credit_SOP_v4.pdf
4. 04_Product_Operations_Guide_and_Known_Issues.pdf
5. 05_Northstar_Logistics_Enterprise_Agreement.pdf
6. 06_LumenWorks_Service_Agreement.pdf

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

The app can run without a Groq key, using a deterministic evidence synthesis fallback. For the assessment demo, set `GROQ_API_KEY`.

## Demo users

- Customer: Northstar Logistics / account `NORTHSTAR`
- Customer: LumenWorks / account `LUMENWORKS`
- Internal: Support Agent
- Internal: Operations Manager

These are mock contexts only. The actual account IDs are discovered from the workbook when possible.

## Architecture

```text
Streamlit
   |
   +-- Auth/User Context
   |
   +-- Agent Orchestrator
         |
         +-- Document Search
         |     +-- semantic retrieval
         |     +-- BM25 retrieval
         |     +-- authority/freshness reranking
         |
         +-- Structured Data Lookup
         |     +-- accounts
         |     +-- orders
         |     +-- tickets
         |
         +-- Calculator
         |
         +-- Action Tool
               +-- create escalation
               +-- requires confirmation
```

## Security principle

Permissions are enforced inside tools, not only in prompts. A customer query is filtered by its authenticated `account_id` before returning operational data.

## Source reliability

Customer-specific agreements have highest precedence for that account. Current SOP/policy outranks deprecated material. Historical tickets are contextual only and are never treated as authoritative policy.

## Testing

```bash
pytest -q
```

## Deployment

Streamlit Community Cloud is the easiest deployment path:
1. Push this repository to GitHub.
2. Create a Streamlit app pointing to `app.py`.
3. Add `GROQ_API_KEY` and `GROQ_MODEL` in Secrets.
4. Ensure the assessment PDFs/XLSX are committed if permitted by the assessment terms, or load them through the approved private data mechanism.

## Assessment limitations

This repository intentionally does not invent facts from the missing official data pack. Once the supplied files are added, the same retrieval/data layer handles the real records.


## Demo-ready observability

The chat response exposes an **Agent Activity** panel showing authenticated context, authorization checks, operational lookups, document retrieval, source precedence decisions, action preparation/execution, and confidence. This makes the agent behavior easy to demonstrate in the assessment video.
