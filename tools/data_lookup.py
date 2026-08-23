
from pathlib import Path
import pandas as pd
import re
from security.auth import authorize_record, UserContext

DATA_PATH = Path("data/ParcelPilot_Assessment_Data.xlsx")
DEMO_DATA_PATH = Path("data/sample_demo_data.xlsx")

ALIASES = {
    "account": ["account", "account_id", "customer", "customer_name", "customer_id", "client"],
    "order": ["order", "order_id", "shipment", "shipment_id"],
    "ticket": ["ticket", "ticket_id", "case", "case_id"],
}

_workbook_cache = None

def load_workbook():
    global _workbook_cache
    if _workbook_cache is not None:
        return _workbook_cache
    path = DATA_PATH if DATA_PATH.exists() else DEMO_DATA_PATH
    if not path.exists():
        return {}
    _workbook_cache = pd.read_excel(path, sheet_name=None)
    return _workbook_cache

def normalize(x):
    return re.sub(r"[^a-z0-9]", "", str(x).lower())

def entity_for_sheet(name, df):
    n = normalize(name)
    cols = {normalize(c) for c in df.columns}
    for entity, aliases in ALIASES.items():
        if any(normalize(a) in n for a in aliases):
            return entity
    for entity, aliases in ALIASES.items():
        if any(normalize(a) in cols for a in aliases):
            return entity
    return name.lower()

def _records(df):
    for _, row in df.iterrows():
        yield {str(k): (None if pd.isna(v) else v) for k, v in row.to_dict().items()}

def _id_column(entity):
    return {"order": "order_id", "ticket": "ticket_id", "account": "account_id"}.get(entity)

def lookup(entity: str, query: str, user: UserContext, limit: int = 20):
    sheets = load_workbook()
    if not sheets:
        return {"error": "Assessment workbook not found at data/ParcelPilot_Assessment_Data.xlsx"}

    entity = entity.lower().strip()
    query_norm = normalize(query)
    id_col = _id_column(entity)
    authorized = []
    unauthorized_exact = False
    matched_any = False

    for sheet, df in sheets.items():
        if df.empty or entity_for_sheet(sheet, df) != entity:
            continue

        # Identifier queries are exact on the entity's ID column. This prevents
        # accidental matches against unrelated fields and avoids first-match bugs.
        if id_col and id_col in df.columns:
            candidates = []
            for rec in _records(df):
                if normalize(rec.get(id_col)) == query_norm:
                    candidates.append(rec)
        else:
            candidates = [r for r in _records(df) if query_norm in normalize(" ".join(map(str, r.values())))]

        for rec in candidates:
            matched_any = True
            if authorize_record(user, rec):
                authorized.append(rec)
                if len(authorized) >= limit:
                    break
            else:
                unauthorized_exact = True

        if len(authorized) >= limit:
            break

    if authorized:
        return {"entity": entity, "query": query, "records": authorized}

    # Never reveal whether an exact identifier belongs to another customer.
    if user.role == "customer" and unauthorized_exact:
        return {
            "entity": entity,
            "query": query,
            "records": [],
            "not_found_or_unauthorized": True,
            "security_filtered": True,
        }

    return {
        "entity": entity,
        "query": query,
        "records": [],
        "not_found_or_unauthorized": True,
        "matched_any": matched_any,
    }

def all_authorized_records(entity: str, user: UserContext):
    sheets = load_workbook()
    out = []
    for sheet, df in sheets.items():
        if df.empty or entity_for_sheet(sheet, df) != entity:
            continue
        for rec in _records(df):
            if authorize_record(user, rec):
                out.append(rec)
    return out


def get_dataset_snapshot():
    sheets = load_workbook()
    df = sheets.get("README")
    if df is None or df.empty:
        return None
    for _, row in df.iterrows():
        values = list(row.values)
        if values and str(values[0]).strip().lower() == "dataset snapshot":
            return values[1] if len(values) > 1 else None
    return None
