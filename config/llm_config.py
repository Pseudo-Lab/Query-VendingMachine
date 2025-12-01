"""
LangChain LLM 설정 모듈

OpenAI의 ChatOpenAI를 LangChain으로 래핑한 설정을 제공합니다.
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# .env 환경변수 불러오기
load_dotenv()

# OpenAI API 키
API_KEY = os.getenv("OPENAI_API_KEY")

# LangChain ChatOpenAI 인스턴스 생성
# 모델: gpt-4o-mini
# temperature: 0.2 (낮은 값으로 일관된 SQL 생성)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=API_KEY,
    temperature=0.2,
)


def get_llm():
    """
    LLM 인스턴스 반환

    Returns:
        ChatOpenAI: LangChain의 ChatOpenAI 인스턴스
    """
    return llm
