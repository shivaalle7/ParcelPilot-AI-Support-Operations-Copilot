# Architecture Note

## Agent design

The system uses one orchestrated support agent rather than a swarm of autonomous agents. The agent chooses among deterministic tools for document search, operational lookup, calculation, and state-changing actions. This reduces coordination complexity and makes permissions and auditing easier.

## Tool design

1. `search_documents` — searches policies, SOPs, product documentation and agreements.
2. `lookup_operational_data` — retrieves accounts, orders and tickets from structured data.
3. `calculate_delay_and_credit` — performs deterministic time/SLA calculations.
4. `prepare_escalation` / `create_escalation` — prepares and executes a mock state-changing action.

Actions are split into prepare and execute. Execute is only available after explicit user confirmation.

## Document handling

PDFs are extracted with PyMuPDF and chunked with overlap. Each chunk receives metadata including source type, customer, status, authority and source name. Semantic retrieval uses SentenceTransformers when available; BM25 provides lexical retrieval for IDs and exact policy terms.

## Structured-data handling

The workbook is loaded dynamically. Sheets are normalized into logical entities when recognizable by column names. The lookup layer accepts flexible column names and performs exact/partial matching.

## Reliability and conflicts

Authority ranking:

1. Customer-specific agreement
2. Current SOP/policy
3. Current product documentation
4. Deprecated documentation
5. Historical ticket resolutions

When conflicting evidence is retrieved, the higher-authority current source wins. If conflict remains unresolved, the agent reports uncertainty and recommends human review.

## Access control

Customer data tools require the authenticated account context and reject records belonging to other accounts. Internal roles have broader access. Authorization is implemented in Python before data is returned to the model.

## Major trade-offs

A single orchestrator is easier to test and observe than a multi-agent swarm. Deterministic calculations are preferred over LLM arithmetic. The LLM is used for interpretation and synthesis, while code owns permissions and actions.
