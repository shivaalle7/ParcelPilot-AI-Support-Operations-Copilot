import os
import streamlit as st
from dotenv import load_dotenv
import importlib

# Force reload internal modules to pick up changes in Streamlit
import security.auth
importlib.reload(security.auth)
import tools.data_lookup
importlib.reload(tools.data_lookup)
import agents.graph
importlib.reload(agents.graph)
import analytics.issue_detection
importlib.reload(analytics.issue_detection)

from security.auth import get_user_context, render_user_selector
from agents.graph import run_langgraph_agent, pending_action_from_state
from analytics.issue_detection import build_issue_summary, render_operations_dashboard
from retrieval.ingest import ensure_index

load_dotenv()

st.set_page_config(page_title="ParcelPilot AI Copilot", page_icon="📦", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1280px; padding-top: 1.2rem;}
[data-testid="stMetricValue"] {font-size: 1.55rem;}
.evidence {padding:10px;border-left:4px solid #64748b;background:#f8fafc;margin:6px 0;}
.hero {padding:16px 18px;border-radius:12px;background:#f8fafc;border:1px solid #e2e8f0;margin-bottom:14px;}
</style>
""", unsafe_allow_html=True)

st.title("📦 ParcelPilot AI Support & Operations Copilot")
st.markdown('<div class="hero"><b>How can I help?</b><br>Ask about your shipment, cancellation, service credit, ticket, or support policy. I’ll check the relevant ParcelPilot records and explain the answer clearly.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("User Context")
    mode, account_name, role = render_user_selector()
    user = get_user_context(mode, account_name, role)

index = ensure_index()

tabs = st.tabs(["💬 Support Copilot", "📊 Operations Intelligence", "🔐 Security & Design"])

with tabs[0]:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Ask about an order, policy, agreement, ticket, SLA, or issue...")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Investigating..."):
                result = run_langgraph_agent(prompt, user, index=index)
            st.markdown(result["answer"])

            # Keep sources available without cluttering the customer conversation.
            if result.get("evidence"):
                with st.expander("View supporting information"):
                    import ast
                    import pandas as pd
                    order_info = None
                    for e in result["evidence"]:
                        if e.get("source") == "Structured order data":
                            content = e.get("content")
                            try:
                                if isinstance(content, str):
                                    order_info = ast.literal_eval(content)
                                elif isinstance(content, dict):
                                    order_info = content
                            except Exception:
                                pass
                    
                    if order_info:
                        order_id = order_info.get("order_id")
                        status = order_info.get("status")
                        pickup_actual = order_info.get("pickup_actual_at")
                        pickup_status = "Picked up" if (pickup_actual and not pd.isna(pickup_actual)) else "Not picked up"
                        acc_name = user.account_name if user.role == "customer" else "Internal Support"
                        
                        st.markdown(f"- **Order**: {order_id}")
                        st.markdown(f"- **Account**: {acc_name}")
                        st.markdown(f"- **Order status**: {status}")
                        st.markdown(f"- **Pickup status**: {pickup_status}")
                    
                    seen = set()
                    for e in result["evidence"]:
                        source = e.get("source", "ParcelPilot source")
                        if source in seen or source == "Structured order data":
                            continue
                        seen.add(source)
                        page = e.get("page")
                        page_suffix = f" (Page {page})" if page else ""
                        st.markdown(f"- **Source**: {source}{page_suffix}")

            if result.get("pending_action"):
                st.warning(result["pending_action"]["message"])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirm action", key=f"confirm_{result['pending_action']['id']}"):
                        confirmed = run_langgraph_agent("YES, CONFIRM THE PREPARED ACTION", user, index=index)
                        st.success(confirmed["answer"])
                with c2:
                    if st.button("Cancel action", key=f"cancel_{result['pending_action']['id']}"):
                        st.info("Action cancelled.")
            st.session_state.messages.append({
                "role":"assistant","content":result["answer"],"tools":result.get("tools",[])
            })

with tabs[1]:
    if role not in ("support_agent", "operations_manager"):
        st.info("Operations Intelligence is available to authorised internal users.")
    else:
        render_operations_dashboard()

with tabs[2]:
    st.subheader("Design principles")
    cols = st.columns(3)
    cols[0].metric("Primary source", "Customer agreement")
    cols[1].metric("Action safety", "Confirmation required")
    cols[2].metric("Security", "Tool-layer RBAC")
    st.markdown("""
**Source precedence:** customer agreement → current SOP/policy → current product docs → deprecated docs → historical tickets.

**Reliability:** conflicting or incomplete evidence results in explicit uncertainty and human escalation rather than fabricated certainty.

**Action model:** actions are prepared first; execution requires explicit confirmation.

**Data privacy:** customer tools filter by authenticated account context before records reach the model.
""")
