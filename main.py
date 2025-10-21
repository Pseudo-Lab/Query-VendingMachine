from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import pandas as pd
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
API_KEY = os.getenv("OPENAI_API_KEY")  # 개인 api 키
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


def get_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    # dims: 1536
    response = client.embeddings.create(input=text, model=model)
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
        v["column_name"]: {
            "data_type": v["data_type"],
            "is_nullable": v["is_nullable"],
            "column_default": v["column_default"],
        }
        for v in result
    }

    return column_dict


def extract_full_schema():
    """전체 데이터베이스 스키마와 관계 정보를 추출"""

    # 1. 모든 테이블 목록 조회
    tables_query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
    """

    # 2. 외래키 관계 조회
    foreign_keys_query = """
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY';
    """

    # 3. 인덱스 정보 조회
    indexes_query = """
    SELECT
        schemaname,
        tablename,
        indexname,
        indexdef
    FROM pg_indexes
    WHERE schemaname = 'public';
    """

    return {
        "tables": run_query(tables_query),
        "foreign_keys": run_query(foreign_keys_query),
        "indexes": run_query(indexes_query),
    }


def format_columns(columns):
    """컬럼 정보를 읽기 쉬운 형태로 포맷팅"""
    formatted = []
    for col_name, col_info in columns.items():
        nullable = "NULL" if col_info["is_nullable"] == "YES" else "NOT NULL"
        default = (
            f" DEFAULT {col_info['column_default']}"
            if col_info["column_default"]
            else ""
        )
        formatted.append(f"  - {col_name}: {col_info['data_type']} {nullable}{default}")
    return "\n".join(formatted)


def format_relationships(relationships):
    """관계 정보를 읽기 쉬운 형태로 포맷팅"""
    if not relationships:
        return "  - No foreign key relationships"

    formatted = []
    for rel in relationships:
        formatted.append(f"  - {rel['column']} -> {rel['references']}")
    return "\n".join(formatted)


def make_table_desc_dict():
    # dvdrental 속 테이블들에 대한 간단한 설명을 작성한 메타 정보.
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


def create_comprehensive_doc():
    """전체 데이터베이스 스키마를 하나의 포괄적인 문서로 생성"""

    schema_info = extract_full_schema()
    table_desc_dict = make_table_desc_dict()

    # 각 테이블의 상세 정보 수집
    tables_detail = {}
    for table in schema_info["tables"]:
        table_name = table["table_name"]
        tables_detail[table_name] = {
            "description": table_desc_dict.get(table_name, ""),
            "columns": extract_ddl(table_name),
            "foreign_keys": [
                fk
                for fk in schema_info["foreign_keys"]
                if fk["table_name"] == table_name
            ],
        }

    # 관계 정보 생성
    relationships = {}
    for fk in schema_info["foreign_keys"]:
        table = fk["table_name"]
        if table not in relationships:
            relationships[table] = []
        relationships[table].append(
            {
                "column": fk["column_name"],
                "references": f"{fk['foreign_table_name']}.{fk['foreign_column_name']}",
            }
        )

    # 포괄적인 문서 생성
    comprehensive_doc = f"""
<Database Schema Overview>

This is a DVD rental database with the following tables and relationships:

"""

    for table_name, info in tables_detail.items():
        comprehensive_doc += f"""
<Table: {table_name}>
Description: {info['description']}

Columns:
{format_columns(info['columns'])}

Relationships:
{format_relationships(relationships.get(table_name, []))}

</Table: {table_name}>

"""

    return comprehensive_doc


def add_join_examples():
    """일반적인 JOIN 패턴 예제를 문서에 추가"""

    join_examples = """
<Common JOIN Patterns>

1. Customer to Address:
   SELECT c.first_name, c.last_name, a.address 
   FROM customer c 
   JOIN address a ON c.address_id = a.address_id;

2. Film to Category:
   SELECT f.title, c.name as category 
   FROM film f 
   JOIN film_category fc ON f.film_id = fc.film_id 
   JOIN category c ON fc.category_id = c.category_id;

3. Rental with Customer and Film (CORRECT PATH):
   SELECT r.rental_date, c.first_name, f.title 
   FROM rental r 
   JOIN customer c ON r.customer_id = c.customer_id 
   JOIN inventory i ON r.inventory_id = i.inventory_id 
   JOIN film f ON i.film_id = f.film_id;

4. Payment with Customer and Staff:
   SELECT p.amount, c.first_name, s.first_name as staff_name
   FROM payment p
   JOIN customer c ON p.customer_id = c.customer_id
   JOIN staff s ON p.staff_id = s.staff_id;

5. Film with Actors:
   SELECT f.title, a.first_name, a.last_name
   FROM film f
   JOIN film_actor fa ON f.film_id = fa.film_id
   JOIN actor a ON fa.actor_id = a.actor_id;

6. Most Rented Films (CORRECT):
   SELECT f.title, COUNT(*) AS rental_count 
   FROM rental r 
   JOIN inventory i ON r.inventory_id = i.inventory_id 
   JOIN film f ON i.film_id = f.film_id 
   GROUP BY f.title 
   ORDER BY rental_count DESC 
   LIMIT 10;

7. Customer Rental History:
   SELECT c.first_name, c.last_name, f.title, r.rental_date
   FROM customer c
   JOIN rental r ON c.customer_id = r.customer_id
   JOIN inventory i ON r.inventory_id = i.inventory_id
   JOIN film f ON i.film_id = f.film_id
   ORDER BY c.last_name, r.rental_date DESC;

8. Films by Category with Rental Count:
   SELECT cat.name as category, f.title, COUNT(r.rental_id) as rental_count
   FROM film f
   JOIN film_category fc ON f.film_id = fc.film_id
   JOIN category cat ON fc.category_id = cat.category_id
   JOIN inventory i ON f.film_id = i.film_id
   JOIN rental r ON i.inventory_id = r.inventory_id
   GROUP BY cat.name, f.title
   ORDER BY cat.name, rental_count DESC;

</Common JOIN Patterns>

<Critical Database Relationships - MUST FOLLOW THESE PATHS>
- rental.inventory_id → inventory.inventory_id
- inventory.film_id → film.film_id
- rental.customer_id → customer.customer_id
- rental.staff_id → staff.staff_id
- film.film_id → film_category.film_id
- film_category.category_id → category.category_id
- film.film_id → film_actor.film_id
- film_actor.actor_id → actor.actor_id
- customer.address_id → address.address_id
- staff.address_id → address.address_id
- address.city_id → city.city_id
- city.country_id → country.country_id

IMPORTANT: rental table does NOT have film_id column directly!
To get film information from rental, you MUST go through inventory table:
rental → inventory → film

</Critical Database Relationships>

<Common Query Patterns>
- Most rented films: rental → inventory → film
- Customer rental history: customer → rental → inventory → film
- Films by category: film → film_category → category
- Films with actors: film → film_actor → actor
- Customer payments: customer → payment → staff

</Common Query Patterns>
"""

    return join_examples


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
        {"name": name, "description": doc_text, "embedding": embedding},
    )


def insert_comprehensive_doc():
    """포괄적인 데이터베이스 문서를 생성하고 임베딩으로 저장"""

    # 전체 스키마 문서 생성
    schema_doc = create_comprehensive_doc()

    # JOIN 예제 추가
    join_examples = add_join_examples()

    # 최종 문서
    final_doc = schema_doc + join_examples

    # 임베딩 생성 및 저장
    embedding = get_embedding(final_doc)

    run_command(
        """
        INSERT INTO table_docs (name, description, embedding)
        VALUES (:name, :description, :embedding)
        """,
        {
            "name": "comprehensive_schema",
            "description": final_doc,
            "embedding": embedding,
        },
    )


############################# 초기 테이블 작업: 임베딩 삽입 시작 #############################
if INIT_TABLE_DOCS:
    print("초기 테이블 작업: 임베딩 삽입 시작.")

    # 기존 개별 테이블 문서 생성
    for table in make_table_desc_dict():
        insert_doc(table)

    # 포괄적인 스키마 문서 생성
    insert_comprehensive_doc()

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


def search_docs_enhanced(query: str, limit: int = 3):
    """개선된 문서 검색 - 스키마와 예제 모두 고려"""

    query_emb = get_embedding(query)

    # 포괄적인 스키마 문서와 개별 테이블 문서 모두 검색
    sql = """
        SELECT id, name, description,
               embedding <=> (:query_emb)::vector AS distance
        FROM table_docs
        ORDER BY embedding <=> (:query_emb)::vector
        LIMIT :limit;
    """

    results = run_query(sql, {"query_emb": query_emb, "limit": limit})

    # 결과를 하나의 컨텍스트로 결합
    combined_context = "\n\n".join([r["description"] for r in results])

    return [{"name": "combined", "description": combined_context}]


def clean_sql_output(raw: str) -> str:
    import re

    return re.sub(r"^```sql\n|\n```$", "", raw.strip())


def generate_sql(natural_query: str, limit: int = 3):
    # 1. 유사 테이블 검색 (개선된 버전 사용)
    results = search_docs_enhanced(natural_query, limit=limit)
    context = results[0]["description"] if results else ""

    # 2. LLM 프롬프트 구성
    system_prompt = """You are an expert SQL generator for a DVD rental database.

CRITICAL RULES:
1. rental table does NOT have film_id column directly
2. To get film information from rental, you MUST use: rental → inventory → film
3. Always follow the exact relationship paths provided in the context
4. Use proper JOIN syntax (INNER JOIN, LEFT JOIN, etc.) when needed
5. Do not invent columns that don't exist

You will be given:
1. A natural language query from the user.
2. A comprehensive context that includes:
   - Database schema with all tables, columns, and relationships
   - Common JOIN patterns and examples
   - Foreign key relationships between tables

Your task:
- Generate a valid SQL query that answers the natural language query.
- Use appropriate JOINs when data from multiple tables is needed.
- Use only the provided tables and columns.
- Do not invent tables or columns that are not in the context.
- Return only the SQL query, nothing else.
- ALWAYS follow the relationship paths: rental → inventory → film for film-related queries.
"""

    user_prompt = f"""
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
        temperature=0.3,
        max_completion_tokens=500,
    )
    print("-------")
    print(user_prompt)
    print("-------")

    return resp.choices[0].message.content


if __name__ == "__main__":
    st.title("📝 Text2SQL Demo - Enhanced with JOIN Support")

    natural_query = st.text_input(
        "Enter your question:",
        "Show me all customers who rented films in the Action category with their rental dates and film titles.",
    )

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
