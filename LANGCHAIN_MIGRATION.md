# LangChain 마이그레이션 가이드

## 개요

Query VendingMachine 프로젝트에 **LangChain**을 도입하여 코드 구조를 개선하고 RAG(Retrieval-Augmented Generation) 파이프라인을 구현했습니다.

## 주요 개선사항

### 1. 코드 구조화 (Phase 1)
**목표**: 모듈별 책임 분리

```
프로젝트 구조
├── config/
│   └── llm_config.py          # LLM 설정
├── retrievers/
│   └── db_retriever.py         # 벡터 검색 Retriever
├── prompts/
│   └── sql_generation_prompt.py # 프롬프트 템플릿
├── chains/
│   ├── sql_generation_chain.py # 기본 LLM 체인
│   └── text_to_sql_chain.py    # 최종 RAG 체인
├── utils/
│   ├── db_utils.py             # DB 유틸리티
│   └── logging_utils.py        # 로깅 유틸리티
└── main.py                      # Streamlit 앱 (리팩토링)
```

### 2. 프롬프트 템플릿화 (Phase 2)
**이전**: 프롬프트가 `main.py` 내에 하드코딩
```python
# 기존: main.py 내 하드코딩
system_prompt = """You are an expert SQL generator...
"""
```

**이후**: 프롬프트 템플릿 분리
```python
# 신규: prompts/sql_generation_prompt.py
from langchain.prompts import ChatPromptTemplate

def get_sql_generation_prompt():
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT_TEMPLATE),
    ])
```

**장점**:
- 프롬프트 변경 시 `main.py` 수정 불필요
- 프롬프트 버전 관리 용이
- A/B 테스트를 위한 변형 프롬프트 관리 간편

### 3. LLM 래퍼 추상화 (Phase 3)
**이전**: 직접 OpenAI API 호출
```python
# 기존
from openai import OpenAI
client = OpenAI(api_key=API_KEY)
resp = client.chat.completions.create(...)
```

**이후**: LangChain ChatOpenAI 사용
```python
# 신규: config/llm_config.py
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-5-mini")
```

**장점**:
- LLM 변경 용이 (OpenAI → Anthropic, Google 등)
- LCEL을 통한 선언적 체인 구성
- 일관된 인터페이스

### 4. Retriever 표준화 (Phase 4)
**이전**: 순수 함수 기반 검색
```python
# 기존
def search_docs(query: str, limit: int = 10):
    query_emb = get_embedding(query)
    # ... 검색 로직 ...
    return results
```

**이후**: LangChain Retriever 인터페이스
```python
# 신규: retrievers/db_retriever.py
class DVDRentalRetriever(BaseRetriever):
    def _get_relevant_documents(self, query: str) -> List[Document]:
        # ... 검색 로직 ...
        return documents
```

**장점**:
- LangChain 에코시스템 표준 준수
- 하이브리드 검색 추가 용이
- 다른 벡터 DB로 전환 시 코드 변경 최소화

### 5. RAG 파이프라인 통합 (Phase 5)
**이전**: 복잡한 함수 중첩
```python
# 기존
results = search_docs(natural_query)
sql = generate_sql(natural_query)  # 벡터 검색 재호출!
query = clean_sql_output(sql)
rows = run_query(query)
```

**이후**: LCEL 선언적 체인
```python
# 신규: chains/text_to_sql_chain.py
text_to_sql_chain = (
    RunnableLambda(get_context_and_primary_table)
    | prompt
    | llm
    | StrOutputParser()
    | RunnableLambda(clean_sql_output)
)

# 사용
sql = text_to_sql_chain.invoke(question)
```

**장점**:
- 파이프라인 명확성 향상
- 디버깅 및 모니터링 용이
- 향후 재시도, 회로차단 등 기능 추가 간편

## 기술 비교표

| 측면 | 기존 방식 | LangChain 방식 |
|------|---------|--------------|
| **프롬프트 관리** | 하드코딩 | PromptTemplate |
| **LLM 호출** | OpenAI SDK 직접 사용 | ChatOpenAI 래퍼 |
| **벡터 검색** | 순수 함수 | BaseRetriever 상속 |
| **파이프라인** | 함수 중첩 | LCEL (선언적) |
| **LLM 변경** | 코드 수정 필요 | 설정만 변경 |
| **캐싱** | 수동 구현 필요 | 내장 지원 |
| **모니터링** | 수동 로깅 | Callbacks 지원 |

## 사용 예시

### 1. 기본 사용법 (Streamlit)
```bash
# 처음 실행시 (초기 테이블 벡터 임베딩 생성)
INIT_TABLE_DOCS=1 streamlit run main.py

# 이후 실행
streamlit run main.py
```

### 2. 프로그래매틱 사용
```python
from chains.text_to_sql_chain import invoke_text_to_sql_chain

# 자연어 질문 → SQL 변환
sql = invoke_text_to_sql_chain("영화 제목과 개봉년도를 나열해줘")
print(sql)  # SELECT title, release_year FROM film;
```

### 3. 프롬프트 커스터마이징
```python
from prompts.sql_generation_prompt import get_sql_generation_prompt

# 프롬프트 수정
prompt = get_sql_generation_prompt()
# → prompts/sql_generation_prompt.py 파일 직접 수정
```

### 4. LLM 변경
```python
# config/llm_config.py 수정
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-3-sonnet", temperature=0.2)
```

## 성능 고려사항

### 벡터 검색 최적화
```python
# retrievers/db_retriever.py 에서 limit 조정
retriever = get_dvdrental_retriever(limit=5)  # 기본값: 10
```

### 로깅 상세도
```python
# utils/logging_utils.py 에서 로깅 커스터마이징
from langchain_core.callbacks import StdOutCallbackHandler

# 체인에 콜백 추가
chain.invoke(input, config={"callbacks": [StdOutCallbackHandler()]})
```

## 다음 단계 (향후 개선)

1. **Callbacks 통합**: LangChain Callbacks으로 전체 파이프라인 모니터링
2. **캐싱**: SQLAlchemy 기반 캐싱 구현
3. **메모리 관리**: ConversationBufferMemory 추가로 대화형 기능
4. **고급 체인 기능**:
   - 재시도 (Retry) 로직
   - 회로차단 (Fallback) 패턴
   - 동적 프롬프트 선택

## 문제 해결

### Q1: "gpt-4-mini" 모델 오류가 발생합니다
**A**: `config/llm_config.py`에서 모델명을 수정하세요.
```python
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
```

### Q2: 벡터 검색 결과가 부정확합니다
**A**: 
1. 임베딩을 재생성합니다: `INIT_TABLE_DOCS=1 streamlit run main.py`
2. 프롬프트를 조정합니다: `prompts/sql_generation_prompt.py`

### Q3: 속도가 느립니다
**A**:
1. 리트리버 제한을 줄입니다: `limit=5`
2. 모델을 변경합니다: `gpt-3.5-turbo` (더 빠름)

## 참고 자료

- [LangChain 공식 문서](https://python.langchain.com/)
- [LCEL 가이드](https://python.langchain.com/docs/expression_language/)
- [Retriever 인터페이스](https://python.langchain.com/docs/modules/data_connection/retrievers/)
