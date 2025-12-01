"""
EPI-SQL Chain Implementation

4-Step Process:
1. Error-prone instances collection (QSESet)
2. General EPIs generation
3. Contextualized EPIs generation
4. SQL generation with EPIs
"""

from typing import List, Dict, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from config.llm_config import get_llm
from chains.text_to_sql_chain import create_text_to_sql_chain, clean_sql_output
import os
import json

# QSESet 저장 경로
QSESET_PATH = "chains/v_mungyu/epi_sql/qseset.json"


def load_qseset() -> List[Dict]:
    """QSESet (Question-SQL-EPI set) 로드"""
    if os.path.exists(QSESET_PATH):
        with open(QSESET_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_qseset(qseset: List[Dict]):
    """QSESet 저장"""
    os.makedirs(os.path.dirname(QSESET_PATH), exist_ok=True)
    with open(QSESET_PATH, 'w', encoding='utf-8') as f:
        json.dump(qseset, f, ensure_ascii=False, indent=2)


def generate_epi_for_error(question: str, wrong_sql: str, error: str) -> str:
    """
    특정 에러 케이스에 대한 EPI 생성
    
    Args:
        question: 자연어 질문
        wrong_sql: 잘못 생성된 SQL
        error: 에러 메시지
    
    Returns:
        Error-Prevention Instruction
    """
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert in SQL error analysis. Generate concise error-prevention instructions."),
        ("user", """Analyze this SQL error case and generate a clear, actionable error-prevention instruction.

Question: {question}
Wrong SQL: {wrong_sql}
Error: {error}

Generate a single, specific instruction that would prevent this type of error.
Format: "To avoid [error type], [specific guidance]."
Keep it under 50 words.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    epi = chain.invoke({
        "question": question,
        "wrong_sql": wrong_sql,
        "error": error
    })
    return epi.strip()


def find_similar_errors(question: str, qseset: List[Dict], k: int = 3) -> List[Dict]:
    """
    현재 질문과 유사한 에러 케이스 검색
    
    Args:
        question: 현재 질문
        qseset: QSESet
        k: 반환할 유사 케이스 수
    
    Returns:
        유사한 에러 케이스 리스트
    """
    if not qseset:
        return []
    
    # 간단한 키워드 기반 유사도 (임베딩 사용 시 성능 향상 가능)
    # TODO: 실제로는 OpenAI Embeddings + FAISS 사용 권장
    return qseset[:k]  # 임시로 처음 k개 반환


def generate_contextualized_epi(question: str, qseset: List[Dict]) -> str:
    """
    현재 질문에 맞춤화된 EPI 생성
    
    Args:
        question: 현재 질문
        qseset: QSESet
    
    Returns:
        Contextualized EPI
    """
    if not qseset:
        return "Ensure SQL syntax is correct and all table/column names exist in the schema."
    
    similar_cases = find_similar_errors(question, qseset, k=3)
    
    llm = get_llm()
    
    # 유사 케이스 포맷팅
    examples = []
    for i, case in enumerate(similar_cases, 1):
        examples.append(f"Example {i}:\nQuestion: {case['question']}\nEPI: {case['epi']}")
    examples_text = "\n\n".join(examples)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You generate contextualized error-prevention instructions for SQL generation."),
        ("user", """Based on these similar error cases, generate a specific error-prevention instruction for the current question.

Similar Error Cases:
{examples}

Current Question: {question}

Generate a concise, actionable instruction (under 50 words) that would help avoid potential errors for this specific question.""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    epi = chain.invoke({
        "examples": examples_text,
        "question": question
    })
    return epi.strip()


def generate_sql_with_epi(question: str, epi: str) -> str:
    """
    EPI를 포함한 프롬프트로 SQL 생성
    
    Args:
        question: 자연어 질문
        epi: Error-Prevention Instruction
    
    Returns:
        생성된 SQL
    """
    base_chain = create_text_to_sql_chain()
    
    # EPI를 질문에 추가
    enhanced_question = f"""{question}

[Error Prevention Guide]
{epi}"""
    
    return base_chain.invoke(enhanced_question)


def create_epi_sql_chain():
    """
    EPI-SQL 체인 생성
    
    Returns:
        EPI-SQL Runnable chain
    """
    def _run(question: str) -> str:
        # 1. QSESet 로드
        qseset = load_qseset()
        
        # 2. Contextualized EPI 생성
        epi = generate_contextualized_epi(question, qseset)
        
        # 3. EPI를 포함하여 SQL 생성
        sql = generate_sql_with_epi(question, epi)
        
        return sql
    
    return RunnableLambda(_run)


def invoke_epi_sql_chain(question: str) -> str:
    """
    EPI-SQL 체인 실행
    
    Args:
        question: 자연어 질문
    
    Returns:
        생성된 SQL
    """
    chain = create_epi_sql_chain()
    return chain.invoke(question)


def add_to_qseset(question: str, wrong_sql: str, error: str):
    """
    QSESet에 새로운 에러 케이스 추가
    
    Args:
        question: 질문
        wrong_sql: 잘못된 SQL
        error: 에러 메시지
    """
    qseset = load_qseset()
    
    # EPI 생성
    epi = generate_epi_for_error(question, wrong_sql, error)
    
    # QSESet에 추가
    qseset.append({
        "question": question,
        "wrong_sql": wrong_sql,
        "error": error,
        "epi": epi
    })
    
    save_qseset(qseset)
    return epi
