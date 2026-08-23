\# Architecture Note



\## 1. Agent Design



ParcelPilot AI Support \& Operations Copilot is designed as a reliability-first AI agent that combines document retrieval, structured operational-data lookup, and controlled state-changing actions.



The agent receives a natural-language query and determines which tools are required to answer it.



\### High-Level Flow



User Query

&#x20;   ↓

Streamlit Chat Interface

&#x20;   ↓

AI Agent / Reasoning Layer

&#x20;   ↓

Tool Selection

&#x20;   ↓

Document Retrieval / Operational Data / Actions

&#x20;   ↓

Authorization \& Reliability Checks

&#x20;   ↓

Evidence-Based Reasoning

&#x20;   ↓

Natural-Language Response



The agent supports both simple questions and multi-step requests.



For example, a cancellation question may require:



1\. Looking up the order.

2\. Identifying the customer account.

3\. Retrieving the customer's agreement.

4\. Checking the current cancellation policy/SOP.

5\. Determining whether a cancellation fee applies.

6\. Explaining the answer using the available evidence.



The agent is designed to reason over retrieved evidence rather than relying only on the LLM's general knowledge.



\---



\## 2. Tool Design



The system provides three main tool categories.



\### Document Retrieval Tool



Searches the supplied ParcelPilot documents, including:



\- Current support policy

\- Deprecated support policy

\- Cancellation and service-credit SOP

\- Product operations documentation

\- Customer-specific agreements



The retrieval tool returns relevant evidence to the agent.



\### Operational Data Tool



Queries the structured ParcelPilot workbook containing:



\- Customer accounts

\- Orders

\- Tickets

\- Shipment information

\- SLA/operational information



The agent uses this tool for exact record lookups instead of guessing values.



\### Action Tool



Supports controlled state-changing operations such as:



\- Creating an escalation

\- Updating a ticket

\- Creating a follow-up task



All state-changing actions use a confirmation-first workflow.



The agent prepares the action and asks the user for explicit confirmation before execution.



\---



\## 3. Document and Structured-Data Handling



\### Documents



The supplied PDFs are processed using the following pipeline:



PDFs

&#x20;↓

Text Extraction

&#x20;↓

Chunking

&#x20;↓

Metadata

&#x20;↓

Retrieval Index

&#x20;↓

Relevant Evidence

&#x20;↓

LLM



Document metadata is used to distinguish source type, version, authority, and applicability.



\### Structured Data



The Excel workbook is loaded into structured data using Pandas.



Conceptually:



Accounts

Orders

Tickets

&#x20;  ↓

Operational Data Tool

&#x20;  ↓

Authorized Lookup

&#x20;  ↓

Agent



The LLM does not directly receive unrestricted access to the entire operational dataset.



\---



\## 4. Source Reliability and Conflict Handling



The system intentionally does not treat every source as equally authoritative.



The general source precedence is:



1\. Customer-specific agreement

2\. Current policy/SOP

3\. Current product documentation

4\. Historical ticket resolutions



Deprecated policies are not treated as current governing policies.



Historical ticket resolutions are treated as context only because they may contain incorrect guidance.



When sources conflict, the agent considers:



\- Source authority

\- Document version

\- Current/deprecated status

\- Customer specificity

\- Applicability to the current case



If the conflict cannot be confidently resolved, the system avoids guessing and recommends human review.



\---



\## 5. Security and Access Control



Access control is enforced in the tool/data layer.



For customer-facing requests, the operational-data tool verifies that the requested order, ticket, or account belongs to the authenticated customer context before returning data.



This prevents customers from accessing records belonging to other accounts.



The LLM is therefore not the primary security boundary.



\---



\## 6. Major Technical Trade-offs



\### RAG instead of LLM-only answers



RAG was selected because ParcelPilot's policies, agreements, and operational documentation are domain-specific and can change over time.



Trade-off: Retrieval introduces additional complexity but improves grounding and traceability.



\### Tool-based operational data



Operational data is accessed through controlled tools rather than placing the complete workbook into the prompt.



Trade-off: Tool calls add some latency but provide better accuracy and authorization.



\### Confirmation-first actions



State-changing actions require explicit user confirmation.



Trade-off: This adds an interaction step but reduces the risk of unintended operational changes.



\### Fail-safe behavior



When evidence is insufficient or conflicting, the system prefers uncertainty and escalation over unsupported answers.



This is important for a production support system where incorrect answers can lead to incorrect customer commitments.

