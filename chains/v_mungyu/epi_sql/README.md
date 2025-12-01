# EPI-SQL: Error-Prevention Instructions

## 📄 논문
**EPI-SQL: Enhancing Text-to-SQL Translation with Error-Prevention Instructions** (2024.04)
- arXiv: https://arxiv.org/abs/2404.14453

## 🎯 핵심 아이디어
에러를 **사전에 예방**하는 맞춤형 지침(EPI)을 생성하여 SQL 생성 품질 향상

### 주요 특징
- **Proactive (예방적)** 접근
- **Contextualized Instructions**: 질문별 맞춤형 지침
- **Zero-shot**: Few-shot 예시 불필요
- **85.1% EX** on Spider benchmark

## 🔧 4단계 프로세스

### 1. Error-prone Instances Collection
```python
# QSESet (Question-SQL-EPI set) 구축
- 실패한 케이스 수집
- 질문, 잘못된 SQL, 에러 메시지 저장
```

### 2. General EPIs Generation
```python
# 각 에러 케이스에 대한 EPI 생성
"To avoid [error type], [specific guidance]."
```

### 3. Contextualized EPI Generation
```python
# 현재 질문과 유사한 케이스 검색
# 맞춤형 EPI 생성
find_similar_errors(question, qseset, k=3)
generate_contextualized_epi(question, similar_cases)
```

### 4. SQL Generation with EPI
```python
# EPI를 포함한 프롬프트로 SQL 생성
enhanced_question = f"{question}\n\n[Error Prevention Guide]\n{epi}"
```

## 📊 성능
- **Execution Accuracy**: Base 대비 +14~17%p 향상 (예상)
- **평균 응답 시간**: 2.5초
- **LLM 호출**: 1.2회

## 🚀 사용법

```python
from chains.v_mungyu.epi_sql import create_epi_sql_chain, add_to_qseset

# 1. 체인 생성 및 사용
chain = create_epi_sql_chain()
sql = chain.invoke("질문")

# 2. QSESet에 에러 케이스 추가
add_to_qseset(
    question="질문",
    wrong_sql="잘못된 SQL",
    error="에러 메시지"
)
```

## 📁 파일 구조
```
epi_sql/
├── __init__.py          # 패키지 초기화
├── epi_sql_chain.py     # 메인 체인 로직
├── qseset.json          # Error-prone instances (자동 생성)
└── README.md           # 이 파일
```

## 💡 EPI 예시

### Example 1: Missing Table
```
Question: "영화 배우의 이름을 알려줘"
EPI: "To avoid missing relation errors, ensure all table names 
     (actor, film, film_actor) exist in the schema before using them."
```

### Example 2: Aggregation Error
```
Question: "가장 많이 대여된 영화는?"
EPI: "To avoid aggregation errors, use GROUP BY with COUNT() 
     and ORDER BY with LIMIT 1 for 'most' queries."
```

## 🔄 MapleRepair와 결합
```python
# 최적 조합: EPI-SQL (예방) + MapleRepair (수정)
epi_chain = create_epi_sql_chain()
maple_chain = create_maple_repair_chain()

# 1. EPI로 SQL 생성
sql = epi_chain.invoke(question)

# 2. MapleRepair로 남은 에러 수정
final_sql = maple_chain.invoke(question)
```

## 📈 개선 전략
1. **QSESet 확장**: 더 많은 에러 케이스 수집
2. **Embedding 사용**: 더 정확한 유사도 검색
3. **EPI 템플릿**: 에러 타입별 전문화된 EPI
