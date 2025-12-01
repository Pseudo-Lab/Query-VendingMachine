"""
데이터베이스 벡터 검색 리트리버 모듈

PostgreSQL pgvector를 기반으로 한 커스텀 Retriever를 구현합니다.
기존 search_docs 함수를 LangChain Retriever 인터페이스로 래핑합니다.
"""
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from utils.db_utils import get_embedding, run_query, make_table_desc_dict
from utils.logging_utils import log_step
from typing import List


class DVDRentalRetriever(BaseRetriever):
    """
    PostgreSQL pgvector 기반 커스텀 리트리버

    DVD Rental 데이터베이스의 테이블 메타정보를 벡터 검색으로 찾습니다.
    """

    limit: int = 10  # 검색 결과 제한 개수

    class Config:
        """LangChain config"""
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> List[Document]:
        """
        질의와 유사한 관련 테이블 검색

        Args:
            query (str): 사용자의 자연어 질문

        Returns:
            List[Document]: 관련 테이블 정보를 담은 Document 리스트
        """
        log_step("Step 1: 벡터 검색 시작", {"질문": query, "검색_제한": self.limit})

        # 질의 임베딩 생성
        query_emb = get_embedding(query)
        log_step(
            "1-1: 질문 임베딩 완료",
            {
                "임베딩_모델": "text-embedding-3-small",
                "벡터_차원": len(query_emb),
                "임베딩_샘플": query_emb[:5],
            },
        )

        # 벡터 검색 쿼리
        sql = """
            SELECT id, name, description,
                   embedding <=> (:query_emb)::vector AS distance
            FROM table_docs
            ORDER BY embedding <=> (:query_emb)::vector
            LIMIT :limit;
        """
        results = run_query(sql, {"query_emb": query_emb, "limit": self.limit}, dvd=False)

        log_step(
            "1-2: 벡터 검색 완료",
            {
                "찾은_테이블_개수": len(results),
                "테이블_정보": [
                    {
                        "순위": i + 1,
                        "테이블명": r["name"],
                        "유사도_거리": f"{r['distance']:.4f}",
                        "설명": r["description"][:100] + "...",
                    }
                    for i, r in enumerate(results)
                ],
            },
        )

        # 결과를 LangChain Document로 변환
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

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> List[Document]:
        return self._get_relevant_documents(query, run_manager=run_manager)


def get_dvdrental_retriever(limit: int = 10) -> DVDRentalRetriever:
    """
    DVDRentalRetriever 인스턴스 생성

    Args:
        limit (int): 검색 결과 제한 개수 (기본값: 10)

    Returns:
        DVDRentalRetriever: 리트리버 인스턴스
    """
    return DVDRentalRetriever(limit=limit)
