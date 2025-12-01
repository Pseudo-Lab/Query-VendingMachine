from typing import Dict, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from config.llm_config import get_llm
from chains.text_to_sql_chain import create_text_to_sql_chain, clean_sql_output
from utils import run_query
from .repair_utils import schema_dict, nearest, extract_missing_relation, extract_missing_column

def _validate(sql: str) -> Tuple[bool, str]:
    try:
        run_query("EXPLAIN " + sql, dvd=True)
        return True, ""
    except Exception as e:
        return False, str(e)

def _rule_based(sql: str, err: str, schema: Dict[str, List[str]]):
    rel = extract_missing_relation(err)
    if rel:
        cand = nearest(rel, list(schema.keys()))
        if cand and cand != rel:
            import re as _re
            return _re.sub(r"\\b" + _re.escape(rel) + r"\\b", cand, sql)
    return None

def _llm_repair(sql: str, question: str, err: str, schema: Dict[str, List[str]]):
    items = []
    for t, cols in schema.items():
        items.append(f"{t}: {', '.join(cols)}")
    schema_text = "\n".join(items)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You repair SQL for the dvdrental PostgreSQL database. Return only valid SQL without explanation."),
        ("user", "Question:\n{question}\n\nOriginal SQL:\n{sql}\n\nError:\n{error}\n\nAvailable Schema:\n{schema}\n\nReturn only the corrected SQL.")
    ])
    chain = prompt | get_llm() | StrOutputParser() | RunnableLambda(clean_sql_output)
    return chain.invoke({"question": question, "sql": sql, "error": err, "schema": schema_text})

def _repair_loop(initial_sql: str, question: str, max_rounds: int = 3) -> str:
    ok, err = _validate(initial_sql)
    if ok:
        return initial_sql
    schema = schema_dict()
    sql = initial_sql
    for _ in range(max_rounds):
        fixed = _rule_based(sql, err, schema)
        if fixed:
            ok2, err2 = _validate(fixed)
            if ok2:
                return fixed
            sql, err = fixed, err2
            continue
        fixed2 = _llm_repair(sql, question, err, schema)
        ok3, err3 = _validate(fixed2)
        if ok3:
            return fixed2
        sql, err = fixed2, err3
    return sql

def create_maple_repair_chain():
    base = create_text_to_sql_chain()
    def _run(question: str):
        init_sql = base.invoke(question)
        return _repair_loop(init_sql, question)
    return RunnableLambda(_run)

def invoke_maple_repair_chain(question: str) -> str:
    chain = create_maple_repair_chain()
    return chain.invoke(question)
