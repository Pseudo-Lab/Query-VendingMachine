"""
실험 2: 컬럼 값 분포 정보를 활용한 Text2SQL

기존 스키마 정보 + 컬럼별 값 분포/통계 정보를 함께 활용하여
더 정확한 SQL을 생성하는 실험입니다.

예: "Penelope" 같은 실제 값이 first_name 컬럼에 있다는 것을 알 수 있음
"""
import os
import pandas as pd
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config.llm_config import get_llm
from retrievers.db_retriever import get_dvdrental_retriever
from chains.text_to_sql_chain import format_docs, clean_sql_output
from utils import run_query, log_step
from utils.column_stats import (
    collect_all_tables_meta,
    save_meta_to_pickle,
    load_meta_from_pickle,
    format_tables_meta_for_prompt,
)

# 파일 경로
META_PATH = "experiments/experiment_2/table_meta.pkl"
RESULT_PATH = "experiments/experiment_2/result.csv"


# ========== 프롬프트 템플릿 (값 분포 정보 포함) ==========

SYSTEM_PROMPT_V2 = """You are an expert SQL generator for the DVD rental database (dvdrental).

Your task is to generate valid SQL queries based on natural language questions.

You have access to:
1. Table schemas (DDL information)
2. Column metadata (actual values, distributions, ranges)

Rules:
1. Use only the provided tables and columns from the schema information.
2. Use the column metadata to understand what actual values exist in the database.
3. When filtering by specific values (e.g., names, categories), use the EXACT values shown in the metadata.
4. Pay attention to [ID] columns - they are primary keys.
5. Use categorical columns' "values" or "top" to match exact string values.
6. Use JOIN operations to combine multiple tables if needed.
7. Return ONLY the SQL query, nothing else - no explanations or markdown formatting.
8. Ensure the SQL is valid and can be executed on PostgreSQL."""

USER_PROMPT_V2 = """<PrimaryTable>
{primary_table}
</PrimaryTable>

<Question>
{question}
</Question>

<AvailableTables>
{context}
</AvailableTables>

<ColumnMetadata>
{column_meta}
</ColumnMetadata>

Generate a valid SQL query to answer the question. 
Use the column metadata to ensure correct value matching (exact string values, proper ranges, etc.)."""


def get_sql_generation_prompt_v2():
    """실험2용 프롬프트 템플릿 (값 분포 정보 포함)"""
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_V2),
        ("user", USER_PROMPT_V2),
    ])


def ensure_meta_exists() -> dict:
    """메타정보 파일이 없으면 생성, 있으면 로드"""
    if not os.path.exists(META_PATH):
        log_step("📊 테이블 메타정보 수집 시작 (최초 1회)")
        meta = collect_all_tables_meta()
        save_meta_to_pickle(meta, META_PATH)
        log_step("✅ 메타정보 pickle 저장 완료", {"경로": META_PATH})
    else:
        log_step("📂 기존 메타정보 로드", {"경로": META_PATH})
    return load_meta_from_pickle(META_PATH)


def create_text_to_sql_chain_v2(all_meta: dict):
    """
    실험2용 Text2SQL 체인 생성
    
    컬럼 메타정보를 프롬프트에 포함하여 더 정확한 SQL 생성
    """
    retriever = get_dvdrental_retriever(limit=10)
    prompt = get_sql_generation_prompt_v2()
    llm = get_llm()

    def get_context_with_meta(question: str):
        """리트리버 결과 + 컬럼 메타정보 추출"""
        docs = retriever.invoke(question)
        context = format_docs(docs)
        primary_table = docs[0].metadata['table_name'] if docs else ""
        
        # 검색된 테이블들의 컬럼 메타정보 (상위 5개 테이블만)
        table_names = [doc.metadata['table_name'] for doc in docs[:5]]
        column_meta = format_tables_meta_for_prompt(table_names, all_meta)
        
        return {
            "context": context,
            "primary_table": primary_table,
            "question": question,
            "column_meta": column_meta,
        }

    chain = (
        RunnableLambda(get_context_with_meta)
        | prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(clean_sql_output)
    )

    return chain


def invoke_text_to_sql_v2(question: str, all_meta: dict) -> str:
    """실험2용 Text2SQL 실행"""
    log_step("🚀 실험2 SQL 생성 시작", {"질문": question})
    chain = create_text_to_sql_chain_v2(all_meta)
    sql = chain.invoke(question)
    log_step("✅ SQL 생성 완료", {"SQL": sql})
    return sql


def run():
    """
    실험 2 실행
    
    Returns:
        pd.DataFrame: 실험 결과
    """
    # 이미 결과가 있으면 로드
    if os.path.exists(RESULT_PATH):
        log_step("📁 기존 결과 파일 로드")
        return pd.read_csv(RESULT_PATH)

    # 1. 테이블 메타정보 수집/로드
    log_step("📊 실험 2 시작: 컬럼 메타정보 활용 Text2SQL")
    all_meta = ensure_meta_exists()

    # 2. 테스트셋 로드
    testset = pd.read_csv("experiments/dvdrental_testset.csv")
    questions = testset["question"].tolist()

    # 3. 각 질문에 대해 SQL 생성 및 실행
    infer = []
    infer_sql = []

    for i, natural_query in enumerate(questions):
        log_step(f"📝 처리 중 ({i+1}/{len(questions)})", {"질문": natural_query})
        try:
            sql = invoke_text_to_sql_v2(natural_query, all_meta)
            infer_sql.append(sql)
            
            rows = run_query(query=sql, dvd=True)
            df = pd.DataFrame(rows)
            value = df.iloc[0, 0] if not df.empty else None
            infer.append(str(value) if value is not None else "")

        except Exception as e:
            log_step("❌ 오류 발생", {
                "에러_타입": type(e).__name__,
                "에러_메시지": str(e),
            })
            infer.append(None)
            infer_sql.append(None)

    # 4. 결과 저장
    testset["infer"] = infer
    testset["infer_sql"] = infer_sql
    
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    testset.to_csv(RESULT_PATH, index=False, encoding="utf-8-sig")
    
    log_step("✅ 실험 2 완료", {"결과_파일": RESULT_PATH})

    return testset


if __name__ == "__main__":
    result = run()
    print(result)
