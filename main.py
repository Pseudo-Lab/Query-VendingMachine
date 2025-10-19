from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# .env 환경변수 불러오기
load_dotenv()

# db
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, echo=True, future=True)

# external api
API_KEY = os.getenv("OPENAI_API_KEY") # 개인 api 키
client = OpenAI(api_key=API_KEY)

# argument - 환경변수로 초기화 여부 확인
INIT_TABLE_DOCS = os.getenv("INIT_TABLE_DOCS", "0") == "1"

def run_query(query: str, params: dict = None):
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]

def run_command(query: str, params: dict = None):
    with engine.begin() as conn:
        conn.execute(text(query), params or {})

def get_embedding(text:str, model:str="text-embedding-3-small") -> list[float]:
    # dims: 1536
    response = client.embeddings.create(
        input=text,
        model=model
    )
    embedding = response.data[0].embedding
    return embedding

def extract_ddl(table_name):
    ddl_query = f"""SELECT 
        column_name, 
        data_type,
        is_nullable,
        column_default
    FROM 
        information_schema.columns
    WHERE 
        table_schema = 'public' AND table_name = '{table_name}';"""
    
    result = run_query(ddl_query)

    column_dict = {
        # ✅ 수정: 리스트 ["column_name"] 대신 v["column_name"] (문자열 값) 사용
        v["column_name"]:{ 
            "data_type": v["data_type"],
            "is_nullable": v["is_nullable"],
            "column_default": v["column_default"]
        } for v in result
    }

    return column_dict

def make_table_desc_dict():
    # dvdrental 속 테이블들에 대한 간단한 설명을 작성한 메타 정보.
    table_desc_dict = { 
        "actor": "contains actors data including first name and last name.",
        "film": "contains films data such as title, release year, length, rating, etc.",
        "film_actor": "contains the relationships between films and actors.",
        "category": "contains film’s categories data.",
        "film_category": "containing the relationships between films and categories.",
        "store": "contains the store data including manager staff and address.",
        "inventory": "stores inventory data.",
        "rental": "stores rental data.",
        "payment": "stores customer’s payments.",
        "staff": "stores staff data.",
        "customer": "stores customer’s data.",
        "address": "stores address data for staff and customers.",
        "city": "stores the city names.",
        "country": "stores the country names."
    }
    return table_desc_dict
    
def insert_doc(name: str):
    """테이블명, DDL, 짧은 설명을 합쳐서 하나의 문서로 저장"""
    # 설명 + DDL 합치기
    table_desc_dict = make_table_desc_dict()
    ddl = extract_ddl(name)
    summary = table_desc_dict[name]
    
    doc_text = f"""
    <Description>
    
    {summary}
    
    </Description>



    <DDL>
    
    {ddl}
    
    </DDL>
    
    """
    embedding = get_embedding(doc_text)

    # UPSERT: 같은 name이 있으면 UPDATE, 없으면 INSERT
    run_command(
        """
        INSERT INTO table_docs (name, description, embedding)
        VALUES (:name, :description, :embedding)
        ON CONFLICT(name) DO UPDATE SET
            description = EXCLUDED.description,
            embedding = EXCLUDED.embedding
        """,
        {"name": name, "description": doc_text, "embedding": embedding}
    )
    

############################# 초기 테이블 작업: 임베딩 삽입 시작 #############################
if INIT_TABLE_DOCS:
    print("초기 테이블 작업: 임베딩 삽입 시작.")
    tables = make_table_desc_dict().keys()
    for table in make_table_desc_dict():
        insert_doc(table)
    print("초기 테이블 작업: 임베딩 삽입 완료.")
#######################################################################################

# 로깅 유틸리티 함수
def log_step(step_name: str, details: dict = None):
    """파이프라인 각 단계의 처리 과정을 로그로 남깁니다"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"\n{'='*80}")
    print(f"[{timestamp}] 🔹 {step_name}")
    print(f"{'='*80}")
    if details:
        for key, value in details.items():
            if isinstance(value, (dict, list)):
                print(f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}")
            else:
                print(f"  {key}: {value}")
    print()

def search_docs(query: str, limit: int = 10):
    # 질의 → 유사 문서 검색 (최대 10개의 관련 테이블 검색)
    log_step("Step 1: 벡터 검색 시작", {"질문": query, "검색_제한": limit})
    
    query_emb = get_embedding(query)
    log_step("1-1: 질문 임베딩 완료", {
        "임베딩_모델": "text-embedding-3-small",
        "벡터_차원": len(query_emb),
        "임베딩_샘플": query_emb[:5]
    })
    
    sql = """
        SELECT id, name, description,
               embedding <=> (:query_emb)::vector AS distance
        FROM table_docs
        ORDER BY embedding <=> (:query_emb)::vector
        LIMIT :limit;
    """
    results = run_query(sql, {"query_emb": query_emb, "limit": limit})
    
    log_step("1-2: 벡터 검색 완료", {
        "찾은_테이블_개수": len(results),
        "테이블_정보": [
            {
                "순위": i+1,
                "테이블명": r["name"],
                "유사도_거리": f"{r['distance']:.4f}",
                "설명": r["description"][:100] + "..."
            }
            for i, r in enumerate(results)
        ]
    })
    return results

def clean_sql_output(raw: str) -> str:
    import re
    return re.sub(r"^```sql\n|\n```$", "", raw.strip())

def generate_sql(natural_query: str, limit: int = 10): # 최대 10개의 테이블 검색
    log_step("🚀 SQL 생성 파이프라인 시작", {"사용자_질문": natural_query})
    
    # 1. 유사 테이블 검색
    results = search_docs(natural_query, limit=limit)
    
    # 모든 관련 테이블의 정보를 컨텍스트로 구성 (조인 쿼리 지원)
    table_contexts = {r["name"]: r["description"] for r in results}
    primary_table = results[0]["name"] if results else ""
    
    log_step("Step 2: 선택된 테이블", {
        "주요_테이블": primary_table,
        "관련_테이블_개수": len(table_contexts),
        "모든_테이블": list(table_contexts.keys()),
        "컨텍스트_총_길이": sum(len(desc) for desc in table_contexts.values())
    })

    # 2. LLM 프롬프트 구성
    system_prompt = """You are an expert SQL generator.
    
    You will be given:
    1. A natural language query from the user.
    2. A list of related tables where each entry includes:
       - A <Description> ... </Description> block: short natural language description of the table.
       - A <DDL> ... </DDL> block: the schema of that table, with column names, data types, and constraints.
    
    Your task:
    - Generate a valid SQL query that answers the natural language query.
    - Use only the provided tables and columns.
    - Do not invent tables or columns that are not in the context.
    - You can use JOIN operations to combine multiple tables if needed.
    - Return only the SQL query, nothing else.
    """

    
    # 모든 테이블의 컨텍스트를 문자열로 구성
    context_text = "\n\n".join([
        f"<Table: {name}>\n{desc}\n</Table: {name}>"
        for name, desc in table_contexts.items()
    ])
    
    user_prompt = f"""
    <PrimaryTable>
    {primary_table}
    </PrimaryTable>

    <Question>
    {natural_query}
    </Question>


    <AvailableTables>
    {context_text}
    </AvailableTables>
    
    """

    log_step("Step 3: LLM 프롬프트 생성 완료", {
        "시스템_프롬프트_길이": len(system_prompt),
        "사용자_프롬프트_길이": len(user_prompt),
        "전체_토큰_추정": (len(system_prompt) + len(user_prompt)) // 4,
        "시스템_프롬프트": system_prompt,
        "사용자_프롬프트": user_prompt
    })

    # 3. OpenAI 호출
    log_step("Step 4: OpenAI API 호출 중...", {
        "모델": "gpt-5-mini",
    })
    
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # temperature=0.2,
        # max_completion_tokens=2000,
    )
    
    sql_response = resp.choices[0].message.content
    log_step("Step 5: LLM 응답 완료", {
        "생성된_SQL_길이": len(sql_response),
        "사용_토큰": resp.usage.prompt_tokens + resp.usage.completion_tokens,
        "프롬프트_토큰": resp.usage.prompt_tokens,
        "완성_토큰": resp.usage.completion_tokens,
        "생성된_SQL": sql_response
    })
    
    return sql_response

if __name__ == "__main__":
    st.title("📝 Text2SQL Demo")

    natural_query = st.text_input("Enter your question:", "List the title and release year of movies.")

    if st.button("Run"):
        log_step("🎯 사용자 요청 시작")
        
        sql = generate_sql(natural_query)
        query = clean_sql_output(sql)
        
        log_step("Step 6: SQL 정리 완료", {
            "원본_SQL_길이": len(sql),
            "정리된_SQL_길이": len(query),
            "정리된_SQL": query
        })
        
        st.code(query, language="sql")

        try:
            log_step("Step 7: SQL 쿼리 실행 중...", {"SQL": query})
            
            rows = run_query(query)
            df = pd.DataFrame(rows)
            
            log_step("Step 8: 쿼리 실행 완료", {
                "반환된_행_수": len(rows),
                "컬럼_수": len(df.columns),
                "컬럼명": list(df.columns)
            })
            
            st.dataframe(df)
            
            log_step("✅ 전체 파이프라인 완료", {
                "최종_결과_행수": len(rows),
                "처리_상태": "성공"
            })
            
        except Exception as e:
            log_step("❌ 쿼리 실행 오류 발생", {
                "에러_타입": type(e).__name__,
                "에러_메시지": str(e)
            })
            st.error(f"Error running query: {e}")