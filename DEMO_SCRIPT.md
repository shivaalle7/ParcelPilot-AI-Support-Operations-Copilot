# 5-Minute Demo Script

## 0:00–0:30 Problem
Explain that ParcelPilot support agents manually search policies, customer agreements, product documentation, tickets and operational records.

## 0:30–1:05 Architecture
Show Streamlit → user context/RBAC → LangGraph orchestrator → document search / structured lookup / calculator / action tool → evidence-first answer.

## 1:05–2:00 Multi-step query
Use an order query such as:
`Can Northstar cancel ORD-1001 without a cancellation fee?`
Show order lookup, agreement/policy retrieval, source precedence and evidence.

## 2:00–2:45 Operational question
Use a delay/service-credit query. Show structured order data plus deterministic delay calculation plus policy retrieval.

## 2:45–3:25 Security
Switch to a customer context and attempt to access an order belonging to another account. Show that the data tool rejects it before the LLM receives the record.

## 3:25–4:00 State-changing action
Ask to escalate a ticket. Show prepared escalation, then explicit confirmation, then execution.

## 4:00–4:35 Proactive issue detection
Open Operations Intelligence. Explain recurring issues, high-severity tickets and multi-customer issue detection.

## 4:35–5:00 Design decisions
Close with:
`I prioritized reliability over autonomous behavior. The LLM reasons over evidence, deterministic code owns calculations and permissions, and state-changing actions require explicit human confirmation.`
