"""
Text2SQL 최종 통합 체인 모듈

벡터 검색(Retrieval)과 LLM을 조합하여 자연어를 SQL로 변환하는
완전한 RAG(Retrieval-Augmented Generation) 파이프라인을 구현합니다.
"""
import re
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from config.llm_config import get_llm
from prompts.sql_generation_prompt import get_sql_generation_prompt
from retrievers.db_retriever import get_dvdrental_retriever
from utils.logging_utils import log_step


def format_docs(docs):
    """
    Document 리스트를 텍스트로 포맷팅

    Args:
        docs (List[Document]): 리트리버가 반환한 Document 리스트

    Returns:
        str: 포맷팅된 테이블 정보 문자열
    """
    formatted_docs = "\n\n".join(
        [
            f"<Table: {doc.metadata['table_name']}>\n{doc.page_content}\n</Table: {doc.metadata['table_name']}>"
            for doc in docs
        ]
    )
    return formatted_docs


def clean_sql_output(raw_sql: str) -> str:
    """
    LLM이 생성한 SQL에서 마크다운 형식 제거

    Args:
        raw_sql (str): LLM이 생성한 원본 SQL

    Returns:
        str: 정리된 SQL
    """
    return re.sub(r"^```sql\n|\n```$", "", raw_sql.strip())


def create_text_to_sql_chain():
    """
    Text2SQL 전체 파이프라인 체인 생성

    Returns:
        Runnable: 최종 체인 (질문 입력 → SQL 출력)
    
    체인 구조:
        1. 입력: {"question": str}
        2. 리트리버로 관련 테이블 검색
        3. 테이블 정보 포맷팅
        4. 프롬프트 템플릿에 주입
        5. LLM으로 SQL 생성
        6. SQL 정리
        7. 출력: 최종 SQL 쿼리
    """
    retriever = get_dvdrental_retriever(limit=10)
    prompt = get_sql_generation_prompt()
    llm = get_llm()

    # 체인 구성 단계별 설명
    log_step("Text2SQL Chain 설정 시작")

    # 1. 리트리버를 통한 관련 테이블 검색 및 포맷팅
    def get_context_and_primary_table(question: str):
        """리트리버 결과에서 context와 primary_table을 추출"""
        docs = retriever.invoke(question)
        context = format_docs(docs)
        primary_table = docs[0].metadata['table_name'] if docs else ""
        return {"context": context, "primary_table": primary_table, "question": question}

    # 2. 최종 체인 구성: 질문 처리 → 프롬프트 → LLM → 출력 파싱 → SQL 정리
    text_to_sql_chain = (
        RunnableLambda(get_context_and_primary_table)
        | prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(clean_sql_output)
    )

    log_step("Text2SQL Chain 설정 완료")

    return text_to_sql_chain


def invoke_text_to_sql_chain(question: str) -> str:
    """
    Text2SQL 체인 실행

    Args:
        question (str): 사용자의 자연어 질문

    Returns:
        str: 생성된 SQL 쿼리
    """
    log_step("🚀 SQL 생성 파이프라인 시작", {"사용자_질문": question})

    chain = create_text_to_sql_chain()
    sql = chain.invoke(question)

    log_step("Step 5: LLM 응답 완료", {"생성된_SQL": sql})

    return sql


# 모듈 로드 시 체인 인스턴스 생성
text_to_sql_chain = create_text_to_sql_chain()
