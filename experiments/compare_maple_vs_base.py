import pandas as pd
import time
from datetime import datetime
from chains.text_to_sql_chain import create_text_to_sql_chain
from v_mungyu.maple_repair_chain import create_maple_repair_chain
from utils import run_query

def _scalar(rows):
    if not rows:
        return None
    r = rows[0]
    if isinstance(r, dict):
        return list(r.values())[0] if r else None
    return r[0] if len(r) > 0 else None

def _exec(sql: str):
    try:
        rows = run_query(sql, dvd=True)
        return True, _scalar(rows), None
    except Exception as e:
        return False, None, str(e)

def _match(expected, actual):
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) < 0.01
    return str(expected).strip().lower() == str(actual).strip().lower()

def main():
    df = pd.read_csv("experiments/dvdrental_testset.csv")
    base = create_text_to_sql_chain()
    maple = create_maple_repair_chain()
    records = []
    b_ok = 0
    m_ok = 0
    for _, row in df.iterrows():
        q = row["question"]
        label = row["label"]
        b_sql = base.invoke(q)
        ok_b, val_b, err_b = _exec(b_sql)
        b_match = ok_b and _match(label, val_b)
        if b_match:
            b_ok += 1
        time.sleep(0.2)
        m_sql = maple.invoke(q)
        ok_m, val_m, err_m = _exec(m_sql)
        m_match = ok_m and _match(label, val_m)
        if m_match:
            m_ok += 1
        records.append({
            "question": q,
            "expected": label,
            "base_sql": b_sql,
            "base_result": val_b,
            "base_match": b_match,
            "base_error": err_b,
            "maple_sql": m_sql,
            "maple_result": val_m,
            "maple_match": m_match,
            "maple_error": err_m,
        })
        time.sleep(0.3)
    base_acc = b_ok / len(df) * 100 if len(df) else 0
    maple_acc = m_ok / len(df) * 100 if len(df) else 0
    out_df = pd.DataFrame(records)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"experiments/evaluation/compare_maple_vs_base_{ts}.csv"
    import os
    os.makedirs("experiments/evaluation", exist_ok=True)
    out_df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"BASE_ACC={base_acc:.2f}% MAPLE_ACC={maple_acc:.2f}%")
    print(f"SAVED={path}")

if __name__ == "__main__":
    main()
