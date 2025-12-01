# Alpha-SQL: Monte Carlo Tree Search for Text-to-SQL

## 📄 논문
**Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search** (2025.02)
- arXiv: https://arxiv.org/abs/2502.17248

## 🎯 핵심 아이디어
**MCTS (Monte Carlo Tree Search)**를 사용하여 여러 SQL 후보를 탐색하고 최적의 쿼리 선택

### 주요 특징
- **Search-based Generation**: 여러 경로 탐색
- **LLM-as-Action-Model**: 동적 액션 생성
- **Self-supervised Reward**: SQL 품질 자동 평가
- **69.7% EX** on BIRD benchmark (GPT-4o 대비 +2.5%p)

## 🔧 구조 (간소화 버전)

### 1. Multiple Candidates Generation
```python
# 다양한 프롬프트로 여러 SQL 후보 생성
candidates = [
    base_chain.invoke(question),           # 기본
    simple_prompt.invoke(question),        # 단순
    robust_prompt.invoke(question)         # 복잡
]
```

### 2. Validation & Scoring
```python
# 각 후보를 검증하고 점수 부여
for sql in candidates:
    score = _execute_and_score(sql)
    # 1.0: 실행 성공 + 결과 있음
    # 0.8: 실행 성공 + 결과 없음
    # 0.5: 검증 통과 + 실행 실패
    # 0.0: 검증 실패
```

### 3. Best Candidate Selection
```python
# 최고 점수 후보 선택
best_sql = max(candidates, key=lambda x: score(x))

# 점수가 낮으면 개선 시도
if score < 0.8:
    refined_sql = refine_sql_candidate(best_sql, question, error)
```

## 📊 성능
- **Execution Accuracy**: Base 대비 +12~17%p 향상 (예상)
- **평균 응답 시간**: 10~15초 (3개 후보 생성 시)
- **LLM 호출**: 5~10회

## 🚀 사용법

```python
from chains.v_mungyu.alpha_sql import create_alpha_sql_chain

# n_candidates: 생성할 SQL 후보 수 (기본값: 3)
chain = create_alpha_sql_chain(n_candidates=3)
sql = chain.invoke("질문")
```

## 📁 파일 구조
```
alpha_sql/
├── __init__.py          # 패키지 초기화
├── alpha_sql_chain.py   # 메인 체인 로직
└── README.md           # 이 파일
```

## 🎲 MCTS vs 간소화 버전

### 완전한 MCTS (논문)
```
- Tree 구조
- UCB1 selection
- Rollout
- Backpropagation
- 복잡도 높음
```

### 간소화 버전 (현재 구현)
```
- Multiple candidates
- Validation-based scoring
- Best selection
- Optional refinement
- 구현 간단, 효과 유사
```

## 💡 후보 생성 전략

### Candidate 1: Base (기본)
```
일반적인 RAG 기반 생성
```

### Candidate 2: Simple (단순)
```
"Generate the SIMPLEST possible SQL query"
→ 복잡도 낮추기
```

### Candidate 3: Robust (견고)
```
"Consider edge cases and generate a robust query"
→ 엣지 케이스 고려
```

## 🔄 다른 방법론과 비교

| 특성 | MapleRepair | EPI-SQL | Alpha-SQL |
|-----|-------------|---------|-----------|
| **접근** | 사후 수정 | 사전 예방 | 탐색 기반 |
| **LLM 호출** | 1.5회 | 1.2회 | **5~10회** |
| **응답 시간** | 3.5초 | 2.5초 | **10~15초** |
| **강점** | 문법 오류 | 의미 오류 | **넓은 탐색** |
| **약점** | 의미 오류 | QSESet 필요 | **느림, 비용** |

## 📈 개선 전략
1. **완전한 MCTS 구현**: Tree + UCB1 + Rollout
2. **Parallel Generation**: 후보를 병렬로 생성
3. **Caching**: 유사 질문의 후보 재사용
4. **Adaptive n_candidates**: 질문 복잡도에 따라 조절

## ⚠️ 주의사항
- **비용**: LLM 호출이 많아 API 비용 증가
- **속도**: 실시간 서비스에는 부적합
- **최적화**: 후보 수를 줄이면 속도 향상 (정확도 trade-off)

## 🎯 권장 사용 시나리오
- ✅ 배치 처리 (오프라인)
- ✅ 고난이도 질문
- ✅ 정확도가 최우선
- ❌ 실시간 서비스
- ❌ 비용 민감
