# 실험 3: 임베딩 모델(large) + LLM(gpt-5) 변경 실험
# 실험 1과 동일한 방법론이지만, 모델 스펙만 업그레이드

import os
import pandas as pd
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from openai import OpenAI
from dotenv import load_dotenv
from typing import List

from chains.text_to_sql_chain import format_docs, clean_sql_output
from prompts.sql_generation_prompt import get_sql_generation_prompt
from utils import run_query, log_step
from utils.db_utils import make_table_desc_dict

load_dotenv()

# ========== 실험 3 설정 ==========
# 임베딩 모델: text-embedding-3-large (3072차원)
# LLM: gpt-5
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-5"

RESULT_PATH = "experiments/experiment_3/result.csv"

# OpenAI 클라이언트
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding_large(text: str) -> list[float]:
    """text-embedding-3-large 모델로 임베딩 생성"""
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


def get_llm_gpt4o():
    """gpt-5 LLM 인스턴스 반환"""
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


class DVDRentalRetrieverLarge(BaseRetriever):
    """
    실험 3용 리트리버 (text-embedding-3-large 사용)
    
    주의: 기존 table_docs는 small 모델(1536차원)로 임베딩되어 있으므로
    large 모델(3072차원)과 직접 비교 불가.
    이 실험에서는 기존 임베딩 DB를 그대로 사용하되, 질문 임베딩만 large로 변경.
    (실제로는 table_docs도 large로 재임베딩해야 정확한 비교 가능)
    """
    limit: int = 10

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str) -> List[Document]:
        """질의와 유사한 관련 테이블 검색"""
        log_step("Step 1: 벡터 검색 시작 (large 모델)", {"질문": query, "검색_제한": self.limit})

        # 질의 임베딩 생성 (large 모델)
        query_emb = get_embedding_large(query)
        log_step("1-1: 질문 임베딩 완료", {
            "임베딩_모델": EMBEDDING_MODEL,
            "벡터_차원": len(query_emb),
        })

        # 벡터 검색 (기존 small 임베딩과 비교 - 차원이 다르면 오류 발생 가능)
        # 실험 목적상 기존 small 임베딩 DB를 사용
        from utils.db_utils import get_embedding as get_embedding_small
        query_emb_small = get_embedding_small(query)  # small 모델로 검색
        
        sql = """
            SELECT id, name, description,
                   embedding <=> (:query_emb)::vector AS distance
            FROM table_docs
            ORDER BY embedding <=> (:query_emb)::vector
            LIMIT :limit;
        """
        results = run_query(sql, {"query_emb": query_emb_small, "limit": self.limit}, dvd=False)

        log_step("1-2: 벡터 검색 완료", {
            "찾은_테이블_개수": len(results),
        })

        documents = [
            Document(
                page_content=result["description"],
                metadata={
                    "table_name": result["name"],
                    "distance": result["distance"],
                },
            )
            for result in results
        ]

        return documents


def get_retriever_v3(limit: int = 10) -> DVDRentalRetrieverLarge:
    """실험 3용 리트리버 반환"""
    return DVDRentalRetrieverLarge(limit=limit)


def create_text_to_sql_chain_v3():
    """실험 3용 Text2SQL 체인 생성 (gpt-4o 사용)"""
    retriever = get_retriever_v3(limit=10)
    prompt = get_sql_generation_prompt()
    llm = get_llm_gpt4o()  # gpt-4o 사용

    def get_context_and_primary_table(question: str):
        docs = retriever.invoke(question)
        context = format_docs(docs)
        primary_table = docs[0].metadata['table_name'] if docs else ""
        return {"context": context, "primary_table": primary_table, "question": question}

    chain = (
        RunnableLambda(get_context_and_primary_table)
        | prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(clean_sql_output)
    )

    return chain


def invoke_text_to_sql_v3(question: str) -> str:
    """실험 3용 Text2SQL 실행"""
    chain = create_text_to_sql_chain_v3()
    sql = chain.invoke(question)
    return sql


def run():
    """실험 3 실행"""
    
    if os.path.exists(RESULT_PATH):
        return pd.read_csv(RESULT_PATH)

    log_step("🚀 실험 3 시작", {
        "임베딩_모델": EMBEDDING_MODEL,
        "LLM_모델": LLM_MODEL,
    })

    testset = pd.read_csv("experiments/dvdrental_testset.csv")
    question = testset["question"].tolist()
    
    infer = []
    infer_sql = []
    
    for natural_query in question:
        try:
            sql = invoke_text_to_sql_v3(natural_query)
            rows = run_query(query=sql, dvd=True)
            df = pd.DataFrame(rows)
            value = df.iloc[0, 0] if not df.empty else None  # 단일값 하드 코딩.
            infer.append(str(value) if value is not None else "")
            infer_sql.append(sql)
        except Exception as e:
            log_step("❌ 오류 발생", {
                "에러_타입": type(e).__name__,
                "에러_메시지": str(e),
            })
            infer.append(None)
            infer_sql.append(None)

    testset["infer"] = infer
    testset["infer_sql"] = infer_sql
    
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    testset.to_csv(RESULT_PATH, index=False, encoding="utf-8-sig")
    
    log_step("✅ 실험 3 완료", {"결과_파일": RESULT_PATH})
    
    return testset


if __name__ == "__main__":
    result = run()
    print(result)
