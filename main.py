from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import pandas as pd
import argparse
import os

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

# argument
parser = argparse.ArgumentParser(description="text2sql")
parser.add_argument('-1', '--run_special_task', type=int, default=0, help='특정 테이블 작업 실행 여부 (0: 디폴트, 실행 안함; 1: 실행함)')
args = parser.parse_args()

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

    run_command(
        """
        INSERT INTO table_docs (name, description, embedding)
        VALUES (:name, :description, :embedding)
        """,
        {"name": name, "description": doc_text, "embedding": embedding}
    )
    

############################# 초기 테이블 작업: 임베딩 삽입 시작 #############################
if args.run_special_task == 1:
    print("초기 테이블 작업: 임베딩 삽입 시작.")
    tables = make_table_desc_dict().keys()
    for table in make_table_desc_dict():
        insert_doc(table)
    print("초기 테이블 작업: 임베딩 삽입 완료.")
#######################################################################################


def search_docs(query: str, limit: int = 1):
    # 질의 → 유사 문서 검색
    query_emb = get_embedding(query)
    sql = """
        SELECT id, name, description,
               embedding <=> (:query_emb)::vector AS distance
        FROM table_docs
        ORDER BY embedding <=> (:query_emb)::vector
        LIMIT :limit;
    """
    return run_query(sql, {"query_emb": query_emb, "limit": limit})

def clean_sql_output(raw: str) -> str:
    import re
    return re.sub(r"^```sql\n|\n```$", "", raw.strip())

def generate_sql(natural_query: str, limit: int = 2):
    # 1. 유사 테이블 검색
    results = search_docs(natural_query, limit=limit)
    name = results[0]["name"] if results else ""
    context = results[0]["description"] if results else ""

    # 2. LLM 프롬프트 구성
    system_prompt = """You are an expert SQL generator.
    
    You will be given:
    1. A natural language query from the user.
    2. A context object where each key is a table name and its value is text that includes:
       - A <Description> ... </Description> block: short natural language description of the table.
       - A <DDL> ... </DDL> block: the schema of that table, with column names, data types, and constraints.
    
    Your task:
    - Generate a valid SQL query that answers the natural language query.
    - Use only the provided tables and columns.
    - Do not invent tables or columns that are not in the context.
    - Return only the SQL query, nothing else.
    """

    
    user_prompt = f"""

    <name>
    the name of the table is `{name}` .
    </name>

    <Question>
    {natural_query}
    </Question>


    <Context>
    {context}
    </Context>
    
    """

    # 3. OpenAI 호출
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_completion_tokens=300,
    )
    print("-------")
    print(user_prompt)
    print("-------")
    
    return resp.choices[0].message.content

if __name__ == "__main__":
    st.title("📝 Text2SQL Demo")

    natural_query = st.text_input("Enter your question:", "List the title and release year of movies.")

    if st.button("Run"):
        sql = generate_sql(natural_query)
        query = clean_sql_output(sql)
        st.code(query, language="sql")

        try:
            rows = run_query(query)
            df = pd.DataFrame(rows)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error running query: {e}")