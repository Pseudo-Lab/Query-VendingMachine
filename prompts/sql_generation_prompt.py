"""
SQL 생성 프롬프트 템플릿 모듈

LangChain의 ChatPromptTemplate을 사용하여 SQL 생성을 위한
시스템 프롬프트와 사용자 프롬프트 템플릿을 정의합니다.
"""
from langchain_core.prompts import ChatPromptTemplate

# SQL 생성 시스템 프롬프트
SYSTEM_PROMPT = """You are an expert SQL generator for the DVD rental database (dvdrental).

Your task is to generate valid SQL queries based on natural language questions.

Rules:
1. Use only the provided tables and columns from the schema information.
2. Do not invent tables or columns that are not in the context.
3. Use JOIN operations to combine multiple tables if needed to answer the question.
4. Return ONLY the SQL query, nothing else - no explanations or markdown formatting.
5. Ensure the SQL is valid and can be executed on PostgreSQL.
6. Use standard SQL syntax compatible with PostgreSQL."""

# 사용자 질문 프롬프트 템플릿
USER_PROMPT_TEMPLATE = """<PrimaryTable>
{primary_table}
</PrimaryTable>

<Question>
{question}
</Question>

<AvailableTables>
{context}
</AvailableTables>

Generate a valid SQL query to answer the question."""


def get_sql_generation_prompt():
    """
    SQL 생성용 ChatPromptTemplate 생성

    Returns:
        ChatPromptTemplate: 시스템 프롬프트와 사용자 프롬프트를 포함한 템플릿
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", USER_PROMPT_TEMPLATE),
        ]
    )
