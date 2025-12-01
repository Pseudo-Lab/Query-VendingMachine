from typing import List, Dict
from utils import run_query
import difflib
import re

def list_tables() -> List[str]:
    rows = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name", dvd=True)
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r.get("table_name") or list(r.values())[0])
        else:
            out.append(r[0])
    return out

def list_columns(table: str) -> List[str]:
    rows = run_query("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position", {"t": table}, dvd=True)
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r.get("column_name") or list(r.values())[0])
        else:
            out.append(r[0])
    return out

def schema_dict() -> Dict[str, List[str]]:
    d: Dict[str, List[str]] = {}
    for t in list_tables():
        d[t] = list_columns(t)
    return d

def nearest(name: str, candidates: List[str]):
    m = difflib.get_close_matches(name, candidates, n=1, cutoff=0.6)
    return m[0] if m else None

def extract_missing_relation(error: str):
    m = re.search(r'relation "([^"]+)" does not exist', error, re.IGNORECASE)
    if not m:
        m = re.search(r'table "([^"]+)" does not exist', error, re.IGNORECASE)
    return m.group(1) if m else None

def extract_missing_column(error: str):
    m = re.search(r'column "([^"]+)" does not exist', error, re.IGNORECASE)
    return m.group(1) if m else None
