# 🪏 Query VendingMachine - Text2SQL 실험

> 자연어를 SQL로 변환하는 RAG 기반 Text2SQL 시스템의 다양한 방법론 실험

---

## 📊 실험 개요

DVD 대여 데이터베이스(dvdrental)를 대상으로 자연어 질문을 SQL 쿼리로 변환하는 **4가지 방법론**을 비교 실험합니다.

| 실험 | 핵심 아이디어 | 임베딩 모델 | LLM |
|------|-------------|------------|-----|
| 실험 1 | 기본 RAG | text-embedding-3-small | gpt-5-mini |
| 실험 2 | 컬럼 메타정보 추가 | text-embedding-3-small | gpt-5-mini |
| 실험 3 | 모델 업그레이드 | text-embedding-3-large | gpt-5 |
| 실험 4 | **2단계 프로세스 (벡터 검색 없음)** | - | gpt-5-mini |

---

## 🧪 실험 1: 기본 RAG 파이프라인

### 아이디어
가장 기본적인 RAG(Retrieval-Augmented Generation) 구조로 Text2SQL을 구현합니다.

### 파이프라인
```
자연어 질문
    ↓
[1] 질문 임베딩 (text-embedding-3-small)
    ↓
[2] 벡터 검색 (pgvector) - 유사한 테이블 10개 검색
    ↓
[3] 프롬프트 구성
    - 검색된 테이블 스키마 (DDL)
    - 테이블 설명
    - 사용자 질문
    ↓
[4] LLM SQL 생성 (gpt-5-mini)
    ↓
[5] SQL 실행 & 결과 반환
```

### 프롬프트 구조
```xml
<주요테이블>검색 1위 테이블</주요테이블>
<질문>사용자 질문</질문>
<사용가능한테이블>
  <Table: actor>DDL 정보...</Table>
  <Table: film>DDL 정보...</Table>
  ...
</사용가능한테이블>
```

### 한계점
- 테이블 스키마만 제공하므로 **실제 값**을 알 수 없음
- 예: "Penelope"라는 배우가 있는지, 어떤 컬럼에 있는지 모름
- 값 매칭 오류 가능성 높음

---

## 🧪 실험 2: 컬럼 메타정보 활용

### 아이디어
테이블 스키마에 **컬럼별 실제 값 분포 정보**를 추가하여 더 정확한 SQL 생성을 유도합니다.

### 추가되는 컬럼 메타정보
```python
{
    "actor": {
        "first_name": {
            "distinct_count": 128,
            "is_categorical": True,
            "top_values": ["Penelope", "Nick", "Ed", "Jennifer", ...],
        },
        "actor_id": {
            "distinct_count": 200,
            "is_id": True,
            "range": [1, 200],
        }
    }
}
```

### 파이프라인
```
자연어 질문
    ↓
[1] 질문 임베딩
    ↓
[2] 벡터 검색 (상위 10개 테이블)
    ↓
[3] 프롬프트 구성 ⭐ 차이점
    - 검색된 테이블 스키마
    - 테이블 설명
    - ⭐ 컬럼별 메타정보 (값 분포, top values, 범위 등)
    - 사용자 질문
    ↓
[4] LLM SQL 생성 (gpt-5-mini)
    ↓
[5] SQL 실행 & 결과 반환
```

### 프롬프트 구조
```xml
<PrimaryTable>actor</PrimaryTable>
<Question>사용자 질문</Question>
<AvailableTables>DDL 정보...</AvailableTables>
<ColumnMetadata>
  actor.first_name: categorical, top_values=[Penelope, Nick, ...]
  actor.last_name: categorical, top_values=[Guiness, Wahlberg, ...]
  ...
</ColumnMetadata>
```

### 기대 효과
- 실제 존재하는 값으로 정확한 WHERE 조건 생성
- Categorical vs Numeric 컬럼 구분 가능
- ID 컬럼 인식으로 불필요한 조건 방지

---

## 🧪 실험 3: 모델 업그레이드

### 아이디어
실험 1과 동일한 방법론에서 **모델 스펙만 업그레이드**하여 순수 모델 성능 차이를 측정합니다.

### 변경 사항
| 구분 | 실험 1 | 실험 3 |
|------|--------|--------|
| 임베딩 | text-embedding-3-small (1536차원) | text-embedding-3-large (3072차원) |
| LLM | gpt-5-mini | gpt-5 |

### 파이프라인
실험 1과 동일 (모델만 변경)

### 기대 효과
- 더 정확한 시맨틱 검색 (임베딩 품질 향상)
- 더 정확한 SQL 생성 (LLM 추론 능력 향상)
- 방법론 개선 없이 모델 성능만으로 얼마나 향상되는지 측정

### 주의사항
> ⚠️ 현재 구현에서는 기존 table_docs가 small 모델(1536차원)로 임베딩되어 있어,  
> 질문 임베딩만 large로 변경 시 차원 불일치 문제 발생.  
> 정확한 비교를 위해서는 table_docs도 large 모델로 재임베딩 필요.

---

## 🧪 실험 4: 2단계 Text2SQL (벡터 검색 없음)

### 문제 정의
- 벡터 검색으로 테이블을 찾아도 **컬럼의 실제 값 정보가 부족**
- 대소문자, 띄어쓰기 등의 차이로 정확한 WHERE 조건 생성이 어려움
- 예: "action" vs "Action", "Sci-Fi" vs "SciFi"

### 아이디어
벡터 검색을 사용하지 않고 **2단계 LLM 프로세스**로 더 정확한 SQL을 생성합니다.

### 파이프라인
```
자연어 질문
    ↓
═══════════════════════════════════════
[1단계] 테이블 선택 (LLM)
═══════════════════════════════════════
    ↓
프롬프트:
    - 모든 테이블의 상세 설명
    - 모든 컬럼 정보
    - 테이블 간 조인 관계
    ↓
LLM 응답: {"tables": ["actor", "film", "film_actor"], "reason": "..."}
    ↓
═══════════════════════════════════════
[2단계] SQL 생성 (LLM)
═══════════════════════════════════════
    ↓
프롬프트:
    - 선택된 테이블의 상세 스키마
    - ⭐ 각 컬럼의 실제 값들 (전체 또는 샘플)
    - 조인 관계
    ↓
LLM 응답: SQL 쿼리
    ↓
[3] SQL 실행 & 결과 반환
```

### 1단계 프롬프트 특징
- 모든 14개 테이블의 설명, 컬럼, Primary Key 정보 포함
- 테이블 간 조인 관계 명시 (actor ↔ film_actor ↔ film 등)
- LLM이 필요한 테이블만 선택하도록 유도

### 2단계 프롬프트 특징
```yaml
# 선택된 테이블의 상세 정보

## actor
설명: 배우 정보를 저장하는 테이블

### 컬럼 상세:
**first_name**
  - 설명: 배우 이름
  - 타입: character varying, distinct: 128
  - 가능한 값들: ['Adam', 'Al', 'Albert', 'Angela', ...]

**last_name**
  - 설명: 배우 성
  - 타입: character varying, distinct: 121
  - 가능한 값들: ['Akroyd', 'Allen', 'Astaire', ...]
```

### 기대 효과
- ✅ 벡터 검색의 시맨틱 불일치 문제 해결
- ✅ 정확한 문자열 값 매칭 (대소문자, 띄어쓰기 포함)
- ✅ 조인 관계를 명시적으로 제공하여 정확한 JOIN 생성
- ✅ 필요한 테이블만 선택하여 컨텍스트 효율화

### 트레이드오프
- ⚠️ LLM 호출 2회 필요 (비용/지연 증가)
- ⚠️ 1단계 프롬프트가 길어질 수 있음 (토큰 사용량)

---

## 📈 실험 결과 비교

Streamlit 웹 UI의 **결과 비교** 탭에서 확인 가능:
- 정확도 비교 (정답/오답 수)
- 오답 분석 (틀린 문제별 상세 내용)
- 문항별 정답 현황 비교

---

## 🚀 실행 방법

```bash
# 1. 환경 설정
cp .env.example .env  # OPENAI_API_KEY 설정

# 2. Docker 실행
docker compose build --no-cache
docker compose up -d

# 3. 웹 UI 접속
open http://localhost:8501
```

---

## 📁 프로젝트 구조

```
experiments/
├── dvdrental_testset.csv    # 테스트셋 (질문 + 정답)
├── experiment_1/
│   ├── run.py               # 실험 1 실행 코드
│   └── result.csv           # 실험 1 결과
├── experiment_2/
│   ├── run.py               # 실험 2 실행 코드
│   ├── table_meta.pkl       # 컬럼 메타정보 캐시
│   └── result.csv           # 실험 2 결과
├── experiment_3/
│   ├── run.py               # 실험 3 실행 코드
│   └── result.csv           # 실험 3 결과
└── experiment_4/
    ├── run.py               # 실험 4 실행 코드 (2단계 체인)
    ├── table_schema.py      # 테이블 스키마 + 조인 관계 정의
    ├── table_meta.pkl       # 컬럼 메타정보 캐시
    └── result.csv           # 실험 4 결과
```

---

## 🔮 향후 실험 아이디어

- **Few-shot 예시 추가**: 유사 질문-SQL 쌍을 프롬프트에 포함
- **Self-correction**: 생성된 SQL 실행 후 오류 시 재생성
- **Query Decomposition**: 복잡한 질문을 단계별로 분해
- **Fine-tuning**: 도메인 특화 SQL 생성 모델 학습
- **Hybrid 접근**: 벡터 검색 + LLM 테이블 선택 결합
