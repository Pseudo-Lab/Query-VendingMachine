"""
Alpha-SQL Chain Implementation (Simplified Version)

Simplified MCTS approach:
1. Generate multiple SQL candidates
2. Validate each candidate using EXPLAIN
3. Select the best candidate based on validation
4. Optional: LLM-based refinement

Note: This is a simplified version. Full MCTS implementation would include:
- Tree structure with nodes
- UCB1 selection
- Rollout and backpropagation
"""

from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from config.llm_config import get_llm
from chains.text_to_sql_chain import create_text_to_sql_chain, clean_sql_output
from utils import run_query


def _validate_sql(sql: str) -> Tuple[bool, str]:
    """
    SQL 검증 (EXPLAIN 사용)
    
    Args:
        sql: 검증할 SQL
    
    Returns:
        (성공 여부, 에러 메시지)
    """
    try:
        run_query("EXPLAIN " + sql, dvd=True)
        return True, ""
    except Exception as e:
        return False, str(e)


def _execute_and_score(sql: str) -> float:
    """
    SQL 실행 및 점수 계산
    
    Args:
        sql: 실행할 SQL
    
    Returns:
        점수 (0.0 ~ 1.0)
    """
    # 1. 검증 점수
    is_valid, error = _validate_sql(sql)
    if not is_valid:
        return 0.0
    
    # 2. 실행 점수
    try:
        result = run_query(sql, dvd=True)
        if result:
            return 1.0  # 성공적으로 실행되고 결과 있음
        return 0.8  # 실행 성공했지만 결과 없음
    except Exception:
        return 0.5  # 검증은 통과했지만 실행 실패


def generate_sql_candidates(question: str, n_candidates: int = 3) -> List[str]:
    """
    여러 SQL 후보 생성
    
    Args:
        question: 자연어 질문
        n_candidates: 생성할 후보 수
    
    Returns:
        SQL 후보 리스트
    """
    base_chain = create_text_to_sql_chain()
    llm = get_llm()
    
    candidates = []
    
    # 1. Base chain으로 첫 번째 후보 생성
    sql1 = base_chain.invoke(question)
    candidates.append(sql1)
    
    # 2. 다양한 프롬프트로 추가 후보 생성
    if n_candidates > 1:
        # 변형 1: 더 간단한 쿼리 요청
        prompt2 = ChatPromptTemplate.from_messages([
            ("system", "You are a SQL expert. Generate the SIMPLEST possible SQL query."),
            ("user", "Question: {question}\n\nGenerate a simple, direct SQL query. Return only SQL without explanation.")
        ])
        chain2 = prompt2 | llm | StrOutputParser() | RunnableLambda(clean_sql_output)
        sql2 = chain2.invoke({"question": question})
        candidates.append(sql2)
    
    if n_candidates > 2:
        # 변형 2: 더 복잡한 쿼리 요청
        prompt3 = ChatPromptTemplate.from_messages([
            ("system", "You are a SQL expert. Consider edge cases and generate a robust query."),
            ("user", "Question: {question}\n\nGenerate a comprehensive SQL query that handles edge cases. Return only SQL without explanation.")
        ])
        chain3 = prompt3 | llm | StrOutputParser() | RunnableLambda(clean_sql_output)
        sql3 = chain3.invoke({"question": question})
        candidates.append(sql3)
    
    return candidates


def refine_sql_candidate(sql: str, question: str, error: str = "") -> str:
    """
    SQL 후보 개선
    
    Args:
        sql: 개선할 SQL
        question: 원래 질문
        error: 에러 메시지 (있는 경우)
    
    Returns:
        개선된 SQL
    """
    llm = get_llm()
    
    if error:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a SQL expert. Refine the SQL to fix errors."),
            ("user", "Question: {question}\n\nCurrent SQL: {sql}\n\nError: {error}\n\nGenerate improved SQL. Return only SQL without explanation.")
        ])
        chain = prompt | llm | StrOutputParser() | RunnableLambda(clean_sql_output)
        return chain.invoke({"question": question, "sql": sql, "error": error})
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a SQL expert. Optimize and refine the SQL."),
            ("user", "Question: {question}\n\nCurrent SQL: {sql}\n\nGenerate an optimized version. Return only SQL without explanation.")
        ])
        chain = prompt | llm | StrOutputParser() | RunnableLambda(clean_sql_output)
        return chain.invoke({"question": question, "sql": sql})


def select_best_candidate(candidates: List[str], question: str) -> str:
    """
    최적의 SQL 후보 선택
    
    Args:
        candidates: SQL 후보 리스트
        question: 원래 질문
    
    Returns:
        최적의 SQL
    """
    best_sql = candidates[0]
    best_score = 0.0
    
    for sql in candidates:
        score = _execute_and_score(sql)
        if score > best_score:
            best_score = score
            best_sql = sql
        
        # 완벽한 후보를 찾으면 즉시 반환
        if score >= 1.0:
            return sql
    
    # 최고 점수가 낮으면 개선 시도
    if best_score < 0.8:
        is_valid, error = _validate_sql(best_sql)
        if not is_valid:
            refined = refine_sql_candidate(best_sql, question, error)
            refined_score = _execute_and_score(refined)
            if refined_score > best_score:
                return refined
    
    return best_sql


def create_alpha_sql_chain(n_candidates: int = 3):
    """
    Alpha-SQL 체인 생성 (간소화 버전)
    
    Args:
        n_candidates: 생성할 SQL 후보 수
    
    Returns:
        Alpha-SQL Runnable chain
    """
    def _run(question: str) -> str:
        # 1. 여러 SQL 후보 생성
        candidates = generate_sql_candidates(question, n_candidates)
        
        # 2. 최적의 후보 선택
        best_sql = select_best_candidate(candidates, question)
        
        return best_sql
    
    return RunnableLambda(_run)


def invoke_alpha_sql_chain(question: str, n_candidates: int = 3) -> str:
    """
    Alpha-SQL 체인 실행
    
    Args:
        question: 자연어 질문
        n_candidates: 생성할 SQL 후보 수
    
    Returns:
        생성된 SQL
    """
    chain = create_alpha_sql_chain(n_candidates)
    return chain.invoke(question)
