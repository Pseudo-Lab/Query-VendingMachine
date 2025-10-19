"""
데이터베이스 관련 유틸리티 함수 모듈

PostgreSQL 벡터 검색을 위한 기본 함수들을 제공합니다.
"""
from sqlalchemy import create_engine, text
from openai import OpenAI
import os
from dotenv import load_dotenv

# .env 환경변수 불러오기
load_dotenv()

# 데이터베이스 설정
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL, echo=True, future=True)

# OpenAI API 설정
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)


def run_query(query: str, params: dict = None):
    """
    SQL SELECT 쿼리 실행

    Args:
        query (str): 실행할 SQL 쿼리
        params (dict, optional): 쿼리 파라미터

    Returns:
        list: 쿼리 결과를 딕셔너리 리스트로 반환
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        return [dict(row._mapping) for row in result]


def run_command(query: str, params: dict = None):
    """
    SQL INSERT/UPDATE/DELETE 명령어 실행

    Args:
        query (str): 실행할 SQL 명령어
        params (dict, optional): 쿼리 파라미터
    """
    with engine.begin() as conn:
        conn.execute(text(query), params or {})


def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """
    텍스트를 임베딩 벡터로 변환

    Args:
        text (str): 임베딩할 텍스트
        model (str): 사용할 임베딩 모델 (기본값: text-embedding-3-small, 차원: 1536)

    Returns:
        list[float]: 임베딩 벡터
    """
    response = client.embeddings.create(input=text, model=model)
    embedding = response.data[0].embedding
    return embedding


def extract_ddl(table_name):
    """
    테이블의 DDL(Data Definition Language) 정보 추출

    Args:
        table_name (str): 테이블명

    Returns:
        dict: 컬럼명을 키로 하고 데이터 타입, nullable, default 정보를 값으로 하는 딕셔너리
    """
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
        v["column_name"]: {
            "data_type": v["data_type"],
            "is_nullable": v["is_nullable"],
            "column_default": v["column_default"],
        }
        for v in result
    }

    return column_dict


def make_table_desc_dict():
    """
    데이터베이스의 모든 테이블에 대한 간단한 설명 딕셔너리 생성

    Returns:
        dict: 테이블명을 키로 하고 설명을 값으로 하는 딕셔너리
    """
    table_desc_dict = {
        "actor": "contains actors data including first name and last name.",
        "film": "contains films data such as title, release year, length, rating, etc.",
        "film_actor": "contains the relationships between films and actors.",
        "category": "contains film's categories data.",
        "film_category": "containing the relationships between films and categories.",
        "store": "contains the store data including manager staff and address.",
        "inventory": "stores inventory data.",
        "rental": "stores rental data.",
        "payment": "stores customer's payments.",
        "staff": "stores staff data.",
        "customer": "stores customer's data.",
        "address": "stores address data for staff and customers.",
        "city": "stores the city names.",
        "country": "stores the country names.",
    }
    return table_desc_dict


def insert_doc(name: str):
    """
    테이블의 메타정보(설명 + DDL)를 벡터 임베딩과 함께 저장

    Args:
        name (str): 테이블명
    """
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
        {"name": name, "description": doc_text, "embedding": embedding},
    )
