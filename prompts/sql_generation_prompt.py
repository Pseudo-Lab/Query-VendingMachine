"""
SQL 생성 프롬프트 템플릿 모듈

LangChain의 ChatPromptTemplate을 사용하여 SQL 생성을 위한
시스템 프롬프트와 사용자 프롬프트 템플릿을 정의합니다.
"""
from langchain_core.prompts import ChatPromptTemplate

# SQL 생성 시스템 프롬프트
SYSTEM_PROMPT = """
    당신은 DVD 대여 데이터베이스(dvdrental)를 위한 전문 SQL 생성기입니다.

    당신의 임무는 자연어 질문을 바탕으로 유효한 SQL 쿼리를 생성하는 것입니다.

    규칙:
    1. 제공된 스키마 정보에 있는 테이블과 컬럼만 사용하세요.
    2. 컨텍스트에 존재하지 않는 테이블이나 컬럼을 절대 지어내지 마세요.
    3. 질문을 해결하기 위해 필요하다면 JOIN 연산을 사용하여 여러 테이블을 결합하세요.
    4. 오직 SQL 쿼리만 반환하세요. 그 외의 설명이나 마크다운 포맷팅은 절대 포함하지 마세요.
    5. 생성된 SQL이 유효하고 PostgreSQL에서 실행 가능한지 확인하세요.
    6. PostgreSQL과 호환되는 표준 SQL 문법을 사용하세요.
    """

# 사용자 질문 프롬프트 템플릿
USER_PROMPT_TEMPLATE = """
    <주요테이블>
    {primary_table}
    </주요테이블>

    <질문>
    {question}
    </질문>

    <사용가능한테이블>
    {context}
    </사용가능한테이블>

    위 질문에 답변하기 위한 유효한 SQL 쿼리를 생성하세요.
    """


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
