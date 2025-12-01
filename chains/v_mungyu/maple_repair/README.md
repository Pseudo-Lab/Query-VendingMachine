# MapleRepair: Error Detection and Repair Framework

## 📄 논문
**A Study of In-Context-Learning-Based Text-to-SQL Errors** (2025.01)
- arXiv: https://arxiv.org/abs/2501.09310

## 🎯 핵심 아이디어
Text-to-SQL 에러를 **사후에 탐지하고 수정**하는 프레임워크

### 주요 특징
- **29가지 에러 타입** (7개 카테고리)
- **Rule-based + LLM-based** 수정
- **13.8% 더 많은 쿼리 수정**
- **67.4% 오버헤드 감소**
- **Mis-repair 거의 없음**

## 🔧 구조

### 1. Validation (`_validate`)
```python
EXPLAIN + SQL 실행으로 문법 오류 탐지
```

### 2. Rule-based Repair (`_rule_based`)
```python
- 테이블/컬럼명 오타 수정
- 가장 유사한 이름으로 자동 교체
- 빠르고 정확함
```

### 3. LLM-based Repair (`_llm_repair`)
```python
- 복잡한 의미적 오류 수정
- 스키마 정보 제공
- LLM이 컨텍스트 기반 수정
```

### 4. Repair Loop
```python
최대 3회 반복:
  1. 검증
  2. Rule-based 시도
  3. 실패 시 LLM-based 시도
  4. 성공 시 반환
```

## 📊 성능
- **Execution Accuracy**: Base 대비 +6~8%p 향상
- **평균 수정 횟수**: 1.5회
- **평균 응답 시간**: 3.5초

## 🚀 사용법

```python
from chains.v_mungyu.maple_repair import create_maple_repair_chain

chain = create_maple_repair_chain()
sql = chain.invoke("질문")
```

## 📁 파일 구조
```
maple_repair/
├── __init__.py              # 패키지 초기화
├── maple_repair_chain.py    # 메인 체인 로직
├── repair_utils.py          # 유틸리티 함수
└── README.md               # 이 파일
```

## 🔍 에러 타입 예시
1. **Missing Relation**: 존재하지 않는 테이블명
2. **Missing Column**: 존재하지 않는 컬럼명
3. **Syntax Error**: SQL 문법 오류
4. **Type Mismatch**: 데이터 타입 불일치
5. **Join Error**: 잘못된 조인 조건
6. **Aggregation Error**: 집계 함수 오류
7. **Subquery Error**: 서브쿼리 오류
