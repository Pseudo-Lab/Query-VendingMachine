# Advanced Text-to-SQL Methods

이 디렉토리는 최신 Text-to-SQL 연구를 기반으로 한 세 가지 고급 방법론을 포함합니다.

## 📚 방법론 개요

### 1. **MapleRepair** (2025.01) - 사후 수정
```
chains/v_mungyu/maple_repair/
```
- **접근**: Error Detection & Repair
- **타이밍**: 에러 발생 **후** 수정
- **성능**: Base 대비 +6~8%p
- **특징**: Rule-based + LLM-based 수정

[상세 문서](./maple_repair/README.md)

### 2. **EPI-SQL** (2024.04) - 사전 예방
```
chains/v_mungyu/epi_sql/
```
- **접근**: Error-Prevention Instructions
- **타이밍**: 에러 발생 **전** 예방
- **성능**: Base 대비 +14~17%p (예상)
- **특징**: Contextualized 지침 생성

[상세 문서](./epi_sql/README.md)

### 3. **Alpha-SQL** (2025.02) - 탐색 기반
```
chains/v_mungyu/alpha_sql/
```
- **접근**: Monte Carlo Tree Search
- **타이밍**: SQL **생성** 시 탐색
- **성능**: Base 대비 +12~17%p (예상)
- **특징**: Multiple candidates + Best selection

[상세 문서](./alpha_sql/README.md)

---

## 🎯 방법론 비교

| 방법론 | 논문 연도 | 접근법 | EX 향상 | LLM 호출 | 응답 시간 | 추천도 |
|-------|----------|--------|---------|----------|----------|--------|
| **Base** | - | RAG | - | 1 | 2s | ⭐⭐⭐ |
| **MapleRepair** | 2025.01 | 사후 수정 | +6~8% | 1.5 | 3.5s | ⭐⭐⭐⭐ |
| **EPI-SQL** | 2024.04 | 사전 예방 | +14~17% | 1.2 | 2.5s | ⭐⭐⭐⭐⭐ |
| **Alpha-SQL** | 2025.02 | 탐색 기반 | +12~17% | 5~10 | 10~15s | ⭐⭐⭐⭐ |

---

## 🚀 사용법

### 개별 사용
```python
# MapleRepair
from chains.v_mungyu.maple_repair import create_maple_repair_chain
maple_chain = create_maple_repair_chain()
sql = maple_chain.invoke("질문")

# EPI-SQL
from chains.v_mungyu.epi_sql import create_epi_sql_chain
epi_chain = create_epi_sql_chain()
sql = epi_chain.invoke("질문")

# Alpha-SQL
from chains.v_mungyu.alpha_sql import create_alpha_sql_chain
alpha_chain = create_alpha_sql_chain(n_candidates=3)
sql = alpha_chain.invoke("질문")
```

### 조합 사용 (권장)
```python
# 최적 조합: EPI-SQL + MapleRepair
from chains.v_mungyu.epi_sql import create_epi_sql_chain
from chains.v_mungyu.maple_repair import create_maple_repair_chain

# 1. EPI-SQL로 에러 예방하며 SQL 생성
epi_chain = create_epi_sql_chain()
sql = epi_chain.invoke(question)

# 2. MapleRepair로 남은 에러 수정
# (EPI-SQL 체인 내부에 MapleRepair 통합 가능)
```

---

## 📊 4-Way 비교 실험

Streamlit UI에서 네 가지 방법을 동시에 비교할 수 있습니다:

```bash
streamlit run main.py
```

**"4-Way 비교" 탭**에서:
1. Base (기본)
2. MapleRepair (사후 수정)
3. EPI-SQL (사전 예방)
4. Alpha-SQL (탐색 기반)

을 동시에 실행하고 Execution Accuracy를 비교합니다.

---

## 🎓 논문 출처

### MapleRepair
```
A Study of In-Context-Learning-Based Text-to-SQL Errors
arXiv:2501.09310 (2025)
```

### EPI-SQL
```
EPI-SQL: Enhancing Text-to-SQL Translation with Error-Prevention Instructions
arXiv:2404.14453 (2024)
```

### Alpha-SQL
```
Alpha-SQL: Zero-Shot Text-to-SQL using Monte Carlo Tree Search
arXiv:2502.17248 (2025)
```

---

## 💡 권장 시나리오

### 실시간 서비스
```
Base → EPI-SQL (빠르고 효과적)
```

### 배치 처리
```
Base → EPI-SQL → MapleRepair (최고 정확도)
```

### 고난이도 질문
```
Base → Alpha-SQL (넓은 탐색 공간)
```

### 비용 최적화
```
Base → MapleRepair (최소 LLM 호출)
```

---

## 📈 개선 로드맵

### Phase 1 (현재)
- ✅ 세 가지 방법론 구현
- ✅ 4-Way 비교 실험
- ✅ 문서화

### Phase 2 (다음)
- [ ] EPI-SQL QSESet 확장
- [ ] Alpha-SQL 완전한 MCTS 구현
- [ ] 방법론 조합 최적화

### Phase 3 (미래)
- [ ] Ensemble 방법론
- [ ] Adaptive 체인 선택
- [ ] 실시간 성능 모니터링

---

## 🤝 기여

새로운 방법론 추가 시:
1. `chains/v_mungyu/[method_name]/` 폴더 생성
2. `__init__.py`, `[method_name]_chain.py`, `README.md` 작성
3. `main.py`에 비교 실험 추가
4. 이 README 업데이트

---

## 📞 문의

프로젝트 관련 문의는 이슈를 생성해주세요.
