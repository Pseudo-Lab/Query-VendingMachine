# 4-Way Text-to-SQL 방법론 비교

## 📋 요약

네 가지 Text-to-SQL 방법론의 성능과 특징을 비교합니다:

| 방법론 | 연도 | 접근법 | 타이밍 | EX 향상 | LLM 호출 | 응답 시간 |
|-------|------|--------|--------|---------|----------|----------|
| **Base** | - | RAG 기반 | - | - | 1회 | ~2초 |
| **MapleRepair** | 2025.01 | 에러 수정 | 사후 | +6~8%p | ~1.5회 | ~3.5초 |
| **EPI-SQL** | 2024.04 | 에러 예방 | 사전 | +14~17%p | ~1.2회 | ~2.5초 |
| **Alpha-SQL** | 2025.02 | MCTS 탐색 | 생성 | +12~17%p | 5~10회 | ~10~15초 |

---

## 🎯 방법론 상세

### 1. **Base Chain** (기준선)

#### 파이프라인
```
질문 입력
  ↓
① 벡터 검색 (DVDRentalRetriever)
  - pgvector 기반 코사인 유사도
  - 상위 10개 관련 테이블 반환
  ↓
② 프롬프트 생성
  - 질문 + 스키마 정보
  ↓
③ LLM 호출 (gpt-4o-mini)
  - Temperature: 0.2
  ↓
④ SQL 정리 및 반환
```

#### 특징
- ✅ **장점**: 빠르고 단순 (LLM 1회 호출)
- ✅ **장점**: 비용 효율적
- ❌ **단점**: 스키마 환각 (없는 테이블/컬럼)
- ❌ **단점**: 문법 오류 시 실패
- ❌ **단점**: 재시도 없음

#### 코드 위치
```
chains/text_to_sql_chain.py
```

---

### 2. **MapleRepair Chain** (사후 수정)

#### 논문
**A Study of In-Context-Learning-Based Text-to-SQL Errors** (2025.01)
- arXiv: https://arxiv.org/abs/2501.09310

#### 파이프라인
```
질문 입력
  ↓
① Base Chain 실행
  - 초기 SQL 생성
  ↓
② 검증 (EXPLAIN)
  - 성공 → 즉시 반환 ✅
  - 실패 → 수리 루프 진입
  ↓
③ 수리 루프 (최대 3라운드)
  ├─ Rule-based 수정
  │  - 테이블/컬럼명 오타 자동 수정
  │  - Levenshtein 거리 기반
  │  ↓
  │  검증 → ✅ 성공 시 반환
  │  ↓
  └─ LLM 기반 수정
     - 에러 메시지 + 스키마 제공
     - LLM이 SQL 수정
     ↓
     검증 → ✅ 성공 시 반환
  ↓
최종 SQL 반환
```

#### 특징
- ✅ **장점**: 자가 수정 능력
- ✅ **장점**: Rule-based로 빠른 수정
- ✅ **장점**: 검증 메커니즘 (EXPLAIN)
- ✅ **장점**: 29가지 에러 타입 처리
- ⚠️ **단점**: 의미적 오류는 해결 어려움
- ⚠️ **단점**: LLM 호출 증가 (비용)

#### 코드 위치
```
chains/v_mungyu/maple_repair/
├── maple_repair_chain.py
├── repair_utils.py
└── README.md
```

---

### 3. **EPI-SQL Chain** (사전 예방)

#### 논문
**EPI-SQL: Enhancing Text-to-SQL Translation with Error-Prevention Instructions** (2024.04)
- arXiv: https://arxiv.org/abs/2404.14453

#### 파이프라인
```
질문 입력
  ↓
① QSESet 로드
  - Question-SQL-EPI set
  - 과거 에러 케이스 데이터
  ↓
② 유사 에러 케이스 검색
  - 현재 질문과 유사한 실패 사례 찾기
  - Top-k 검색 (k=3)
  ↓
③ Contextualized EPI 생성
  - 현재 질문에 맞춤화된 에러 예방 지침
  - LLM이 유사 케이스 기반 생성
  ↓
④ EPI 포함 SQL 생성
  - Enhanced Question = 질문 + EPI
  - Base Chain으로 SQL 생성
  ↓
최종 SQL 반환
```

#### 특징
- ✅ **장점**: Proactive (예방적) 접근
- ✅ **장점**: 의미적 오류도 예방 가능
- ✅ **장점**: Zero-shot (Few-shot 불필요)
- ✅ **장점**: 85.1% EX on Spider
- ⚠️ **단점**: QSESet 구축 필요
- ⚠️ **단점**: 초기에는 데이터 부족

#### 코드 위치
```
chains/v_mungyu/epi_sql/
├── epi_sql_chain.py
├── qseset.json (자동 생성)
└── README.md
```

#### EPI 예시
```
Question: "영화 배우의 이름을 알려줘"

EPI: "To avoid missing relation errors, ensure all table names 
     (actor, film, film_actor) exist in the schema before using them."

Enhanced Question:
"영화 배우의 이름을 알려줘

[Error Prevention Guide]
To avoid missing relation errors, ensure all table names 
(actor, film, film_actor) exist in the schema before using them."
```

---

### 4. **Alpha-SQL Chain** (탐색 기반)

#### 논문
**Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search** (2025.02)
- arXiv: https://arxiv.org/abs/2502.17248

#### 파이프라인 (간소화 버전)
```
질문 입력
  ↓
① 여러 SQL 후보 생성 (n=3)
  ├─ Candidate 1: Base Chain (일반)
  ├─ Candidate 2: Simple Prompt (단순)
  └─ Candidate 3: Robust Prompt (견고)
  ↓
② 각 후보 검증 및 점수 부여
  - EXPLAIN 검증
  - 실행 결과 확인
  - 점수: 0.0 ~ 1.0
  ↓
③ 최적 후보 선택
  - 최고 점수 SQL 선택
  - 점수 낮으면 개선 시도
  ↓
최종 SQL 반환
```

#### 특징
- ✅ **장점**: 넓은 탐색 공간
- ✅ **장점**: 다양한 접근 시도
- ✅ **장점**: 69.7% EX on BIRD
- ✅ **장점**: Self-supervised Reward
- ⚠️ **단점**: 느림 (LLM 다수 호출)
- ⚠️ **단점**: 비용 높음
- ⚠️ **단점**: 실시간 부적합

#### 코드 위치
```
chains/v_mungyu/alpha_sql/
├── alpha_sql_chain.py
└── README.md
```

#### 후보 생성 전략
```python
# Candidate 1: Base (일반)
"Generate SQL for this question"

# Candidate 2: Simple (단순)
"Generate the SIMPLEST possible SQL query"

# Candidate 3: Robust (견고)
"Consider edge cases and generate a robust query"
```

---

## 📊 성능 비교

### 예상 결과 (60개 테스트셋 기준)

| 방법론 | EX (%) | 개선폭 | 성공 케이스 | 실패 케이스 |
|-------|--------|--------|------------|------------|
| Base | 48.33 | - | 29/60 | 31/60 |
| MapleRepair | 55.00 | +6.67%p | 33/60 | 27/60 |
| EPI-SQL | 62-65 | +14-17%p | 37-39/60 | 21-23/60 |
| Alpha-SQL | 60-65 | +12-17%p | 36-39/60 | 21-24/60 |

### 비용 및 시간 비교

| 방법론 | LLM 호출 | 응답 시간 | 60개 총 시간 | API 비용 (예상) |
|-------|----------|----------|-------------|----------------|
| Base | 1회 | 2초 | 2분 | $0.10 |
| MapleRepair | 1.5회 | 3.5초 | 3.5분 | $0.15 |
| EPI-SQL | 1.2회 | 2.5초 | 2.5분 | $0.12 |
| Alpha-SQL | 5-10회 | 10-15초 | 10-15분 | $0.50-1.00 |

---

## 🔄 방법론 조합

### 최적 조합 1: EPI-SQL + MapleRepair (추천 ⭐)
```
질문 → EPI-SQL (예방) → MapleRepair (수정) → 최종 SQL
```
- **예상 EX**: 68-72%
- **장점**: 사전 예방 + 사후 수정 = 최강 조합
- **단점**: LLM 호출 ~1.7회

### 최적 조합 2: Alpha-SQL + MapleRepair
```
질문 → Alpha-SQL (탐색) → MapleRepair (수정) → 최종 SQL
```
- **예상 EX**: 65-70%
- **장점**: 넓은 탐색 + 에러 수정
- **단점**: 매우 느림, 비용 높음

---

## 🧪 실험 방법

### 1. 테스트셋 생성
```bash
docker exec text2sql-web python /app/testset.py
```
- 60개 질문 (1단계: 32개, 2단계: 28개)
- CSV 저장: `experiments/dvdrental_testset.csv`

### 2. Streamlit UI에서 4-Way 비교
```bash
streamlit run main.py
```
1. 브라우저: http://localhost:8502
2. **"4-Way 비교"** 탭 클릭
3. **[4-Way 비교 실행]** 버튼 클릭
4. 약 10-15분 대기

### 3. 결과 확인
- 📊 **EX 메트릭** (4개 방법론)
- 📈 **Base 대비 개선폭**
- 📋 **상세 결과 테이블**
- 💾 **CSV 저장**: `experiments/4way_comparison_result.csv`

---

## 📈 실제 예시

### 예시 1: 단순 COUNT 쿼리

**질문**: "영화 테이블의 총 개수는?"

| 방법론 | 생성된 SQL | 결과 | 매칭 |
|-------|-----------|------|------|
| Base | `SELECT COUNT(*) FROM film;` | 1000 | ✅ |
| MapleRepair | `SELECT COUNT(*) FROM film;` | 1000 | ✅ |
| EPI-SQL | `SELECT COUNT(*) FROM film;` | 1000 | ✅ |
| Alpha-SQL | `SELECT COUNT(*) FROM film;` | 1000 | ✅ |

**결과**: 모두 성공 (단순 쿼리)

---

### 예시 2: 테이블명 오타

**질문**: "고객 수는?"

| 방법론 | 생성된 SQL | 결과 | 매칭 |
|-------|-----------|------|------|
| Base | `SELECT COUNT(*) FROM custmer;` ❌ | ERROR | ❌ |
| MapleRepair | `SELECT COUNT(*) FROM customer;` ✅ | 599 | ✅ |
| EPI-SQL | `SELECT COUNT(*) FROM customer;` ✅ | 599 | ✅ |
| Alpha-SQL | `SELECT COUNT(*) FROM customer;` ✅ | 599 | ✅ |

**결과**: MapleRepair가 Rule-based로 수정, EPI-SQL은 예방, Alpha-SQL은 다른 후보 선택

---

### 예시 3: 복잡한 집계 (의미적 오류)

**질문**: "평균 이상으로 대여한 고객 수는?"

| 방법론 | 생성된 SQL | 결과 | 매칭 |
|-------|-----------|------|------|
| Base | `SELECT COUNT(DISTINCT customer_id) FROM rental GROUP BY customer_id HAVING COUNT(*) >= (SELECT AVG(cnt) FROM ...);` ❌ | 잘못된 결과 | ❌ |
| MapleRepair | (검증 통과, 수정 없음) | 잘못된 결과 | ❌ |
| EPI-SQL | `WITH rental_counts AS (SELECT customer_id, COUNT(*) as cnt FROM rental GROUP BY customer_id) SELECT COUNT(*) FROM rental_counts WHERE cnt > (SELECT AVG(cnt) FROM rental_counts);` ✅ | 236 | ✅ |
| Alpha-SQL | (여러 후보 중 올바른 것 선택) ✅ | 236 | ✅ |

**결과**: EPI-SQL과 Alpha-SQL이 의미적 오류 해결

---

## 💡 권장 시나리오

### 실시간 서비스
```
Base → EPI-SQL
```
- 빠르고 효과적
- 비용 효율적

### 배치 처리 (최고 정확도)
```
EPI-SQL → MapleRepair
```
- 사전 예방 + 사후 수정
- 68-72% EX 예상

### 고난이도 질문
```
Alpha-SQL
```
- 넓은 탐색 공간
- 시간 여유 있을 때

### 비용 최적화
```
Base → MapleRepair
```
- 최소 LLM 호출
- 기본적인 오류 수정

---

## 🎓 논문 출처

1. **MapleRepair**: A Study of In-Context-Learning-Based Text-to-SQL Errors (2025.01)
   - arXiv:2501.09310

2. **EPI-SQL**: Enhancing Text-to-SQL Translation with Error-Prevention Instructions (2024.04)
   - arXiv:2404.14453

3. **Alpha-SQL**: Zero-Shot Text-to-SQL using Monte Carlo Tree Search (2025.02)
   - arXiv:2502.17248

---

## 📁 프로젝트 구조

```
chains/v_mungyu/
├── README.md                    # 종합 가이드
├── maple_repair/               # MapleRepair
│   ├── __init__.py
│   ├── maple_repair_chain.py
│   ├── repair_utils.py
│   └── README.md
├── epi_sql/                    # EPI-SQL
│   ├── __init__.py
│   ├── epi_sql_chain.py
│   ├── qseset.json
│   └── README.md
└── alpha_sql/                  # Alpha-SQL
    ├── __init__.py
    ├── alpha_sql_chain.py
    └── README.md
```

---

## 🔧 평가 지표

### Execution Accuracy (EX)
- **정의**: 생성된 SQL의 실행 결과가 정답 라벨과 일치하는 비율
- **계산**: `(정답 개수 / 전체 질문 수) × 100%`

### 매칭 규칙
1. **숫자 비교**: 소수점 2자리로 반올림 후 비교
   ```python
   round(float(expected), 2) == round(float(actual), 2)
   ```

2. **문자열 비교**: 소문자 변환 + 공백 제거 후 완전 일치
   ```python
   str(expected).strip().lower() == str(actual).strip().lower()
   ```

---

## 🚀 향후 개선 방향

### Phase 1 (현재)
- ✅ 4가지 방법론 구현
- ✅ 4-Way 비교 실험
- ✅ 문서화

### Phase 2 (다음)
- [ ] EPI-SQL QSESet 확장 (더 많은 에러 케이스)
- [ ] Alpha-SQL 완전한 MCTS 구현
- [ ] 방법론 조합 최적화

### Phase 3 (미래)
- [ ] Ensemble 방법론
- [ ] Adaptive 체인 선택 (질문 복잡도 기반)
- [ ] 실시간 성능 모니터링

---

## 📞 참고 문서

- [MapleRepair 상세](../chains/v_mungyu/maple_repair/README.md)
- [EPI-SQL 상세](../chains/v_mungyu/epi_sql/README.md)
- [Alpha-SQL 상세](../chains/v_mungyu/alpha_sql/README.md)
- [종합 가이드](../chains/v_mungyu/README.md)
