import pandas as pd
import streamlit as st
from tools.data_lookup import all_authorized_records
from security.auth import UserContext

def _df(records):
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)

def build_issue_summary():
    # Internal-only dashboard uses all available records.
    user = UserContext("Internal Support","operations_manager",None,None)
    tickets = _df(all_authorized_records("ticket", user))
    summary = {
        "tickets": len(tickets),
        "high_severity": 0,
        "sla_risk": 0,
        "recurring": 0,
        "multi_customer": 0,
        "categories": pd.DataFrame()
    }
    if tickets.empty:
        return summary
    cols = {str(c).lower(): c for c in tickets.columns}
    sev = next((c for k,c in cols.items() if "severity" in k or "priority" in k), None)
    issue = next((c for k,c in cols.items() if "issue" in k or "category" in k or "type" in k), None)
    account = next((c for k,c in cols.items() if "account" in k or "customer" in k), None)
    if sev:
        summary["high_severity"] = int(tickets[sev].astype(str).str.lower().isin(["high","critical","p1","p0"]).sum())
    if issue:
        vc = tickets[issue].astype(str).value_counts()
        summary["recurring"] = int((vc >= 3).sum())
        summary["categories"] = vc.head(10).rename_axis("issue").reset_index(name="tickets")
    if account and issue:
        pairs = tickets.groupby(issue)[account].nunique()
        summary["multi_customer"] = int((pairs >= 2).sum())
    return summary

def render_operations_dashboard():
    st.subheader("Operations Intelligence")
    summary = build_issue_summary()
    c = st.columns(5)
    c[0].metric("Open tickets", summary["tickets"])
    c[1].metric("High/Critical", summary["high_severity"])
    c[2].metric("Recurring issues", summary["recurring"])
    c[3].metric("Multi-customer issues", summary["multi_customer"])
    c[4].metric("Trust posture", "Evidence-first")

    if not summary["categories"].empty:
        st.markdown("### Recurring issue patterns")
        st.bar_chart(summary["categories"].set_index("issue"))
    else:
        st.info("No recognizable ticket issue/category column was found in the workbook yet.")

    st.markdown("### Detection rules")
    st.markdown(
        "- **High severity:** priority/severity is High, Critical, P1 or P0.\n"
        "- **Recurring issue:** same issue/category appears at least three times.\n"
        "- **Multi-customer issue:** same issue/category affects at least two accounts.\n"
        "- **SLA risk:** can be added when the workbook exposes explicit SLA deadline fields."
    )
