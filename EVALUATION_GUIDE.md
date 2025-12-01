# 🧪 Text2SQL LLM 성능 평가 가이드

## 📋 목차
1. [평가 프로세스 개요](#평가-프로세스-개요)
2. [테스트셋 생성](#테스트셋-생성)
3. [성능 평가 실행](#성능-평가-실행)
4. [결과 분석](#결과-분석)
5. [고급 평가 방법](#고급-평가-방법)

---

## 🎯 평가 프로세스 개요

### 평가 지표

#### 1. **Exact Match (EM)**
- 생성된 SQL이 정답 SQL과 **정확히 일치**하는지 확인
- 가장 엄격한 평가 기준
- 공백, 대소문자 정규화 후 비교

#### 2. **Execution Accuracy (EX)**
- 생성된 SQL과 정답 SQL의 **실행 결과가 동일**한지 확인
- 실무에서 가장 중요한 지표
- SQL 문법은 다르지만 결과가 같으면 정답

#### 3. **Valid SQL (VS)**
- 생성된 SQL이 **문법적으로 올바른지** 확인
- 실행 가능한 SQL인지 검증
- 에러 없이 실행되면 통과

#### 4. **Generation Time**
- SQL 생성에 걸린 시간
- 실시간 서비스 적용 시 중요

---

## 📝 테스트셋 생성

### 1단계: 비즈니스 테스트셋 생성

```bash
# 테스트셋 생성 스크립트 실행
python business_testset.py
```

**출력:**
```
✅ 비즈니스 테스트셋 생성 완료: experiments/business_testset.csv
📊 총 52개의 테스트 케이스

카테고리별 분포:
customer_analysis        8
content_performance      8
inventory_operations     7
revenue_analysis         7
...
```

### 2단계: 테스트셋 확인

생성된 `experiments/business_testset.csv` 파일 구조:
```csv
question,sql,category,difficulty
"전체 총 매출은 얼마인가요?","SELECT ROUND(SUM(amount), 2) FROM payment;","revenue_analysis","초급"
"VIP 고객 명단을 보여주세요","SELECT c.customer_id, ...","customer_analysis","중급"
```

---

## 🚀 성능 평가 실행

### 방법 1: 전체 평가 (권장)

```bash
# 전체 테스트셋 평가
python evaluate_llm.py
```

### 방법 2: 제한된 평가 (빠른 테스트)

`evaluate_llm.py` 파일 수정:
```python
# 10개만 평가
results_df = evaluator.evaluate_all(limit=10)
```

### 방법 3: Streamlit 웹 인터페이스 사용

```bash
streamlit run main.py
```

웹 브라우저에서:
1. "실험 결과" 탭 클릭
2. "실험 시작" 버튼 클릭
3. 실시간으로 결과 확인

---

## 📊 결과 분석

### 평가 결과 파일

평가 완료 후 `experiments/evaluation/` 폴더에 생성:

#### 1. **상세 결과 CSV** (`results_YYYYMMDD_HHMMSS.csv`)
```csv
question,category,difficulty,ground_truth_sql,generated_sql,exact_match,execution_match,valid_sql,error,generation_time
"전체 총 매출은?","revenue_analysis","초급","SELECT ...","SELECT ...",True,True,True,,1.23
```

#### 2. **리포트 JSON** (`report_YYYYMMDD_HHMMSS.json`)
```json
{
  "timestamp": "2025-11-04T18:00:00",
  "total_cases": 52,
  "metrics": {
    "exact_match": {"count": 35, "percentage": 67.31},
    "execution_accuracy": {"count": 45, "percentage": 86.54},
    "valid_sql": {"count": 48, "percentage": 92.31}
  },
  "by_category": {...},
  "by_difficulty": {...}
}
```

### 콘솔 출력 예시

```
================================================================================
📊 Text2SQL LLM 성능 평가 리포트
================================================================================

📅 평가 시간: 2025-11-04T18:00:00
📝 총 테스트 케이스: 52개

🎯 전체 성능 지표:
  • Exact Match (EM):         35개 (67.31%)
  • Execution Accuracy (EX):  45개 (86.54%)
  • Valid SQL (VS):           48개 (92.31%)
  • 평균 생성 시간:           1.23초

📂 카테고리별 성능:
  • revenue_analysis       : 85.71% (7개)
  • customer_analysis      : 87.50% (8개)
  • inventory_operations   : 85.71% (7개)
  • content_performance    : 87.50% (8개)
  • geographic_analysis    : 100.00% (4개)
  • trends_forecasting     : 66.67% (3개)
  • pricing_strategy       : 100.00% (4개)
  • marketing_promotion    : 100.00% (3개)
  • anomaly_detection      : 50.00% (2개)
  • executive_dashboard    : 80.00% (5개)

⭐ 난이도별 성능:
  • 초급      : 95.00% (20개)
  • 중급      : 85.00% (28개)
  • 고급      : 50.00% (4개)

================================================================================
```

---

## 🔍 결과 해석 가이드

### 좋은 성능 기준

| 지표 | 목표 | 우수 | 보통 | 개선 필요 |
|------|------|------|------|-----------|
| **Execution Accuracy** | 90%+ | 85-90% | 70-85% | <70% |
| **Valid SQL** | 95%+ | 90-95% | 80-90% | <80% |
| **Exact Match** | 70%+ | 60-70% | 50-60% | <50% |
| **Generation Time** | <2초 | 2-3초 | 3-5초 | >5초 |

### 성능 분석 체크리스트

#### ✅ 전체 성능이 좋은 경우
- Execution Accuracy > 85%
- Valid SQL > 90%
- 모든 난이도에서 고른 성능

#### ⚠️ 개선이 필요한 경우
- 고급 난이도 정확도 < 50%
- 특정 카테고리 정확도 < 70%
- Valid SQL < 80% (문법 오류 많음)

#### 🔧 문제 진단

**1. Valid SQL은 높지만 Execution Accuracy가 낮은 경우**
- 문법은 맞지만 잘못된 테이블/컬럼 사용
- 조인 조건 누락
- WHERE 조건 잘못 설정
→ **해결**: 프롬프트에 스키마 정보 강화, Few-shot 예제 추가

**2. 특정 카테고리 성능이 낮은 경우**
- 해당 카테고리의 복잡도가 높음
- 도메인 지식 부족
→ **해결**: 해당 카테고리 Few-shot 예제 추가

**3. 고급 난이도 성능이 낮은 경우**
- 서브쿼리, 윈도우 함수 생성 실패
- 복잡한 조인 처리 어려움
→ **해결**: 더 강력한 LLM 모델 사용 (GPT-4 등)

---

## 🎓 고급 평가 방법

### 1. A/B 테스트: 프롬프트 비교

```python
# evaluate_llm.py 수정

# 프롬프트 A
evaluator_a = Text2SQLEvaluator(testset_path, db_url, prompt_version="v1")
results_a = evaluator_a.evaluate_all()

# 프롬프트 B
evaluator_b = Text2SQLEvaluator(testset_path, db_url, prompt_version="v2")
results_b = evaluator_b.evaluate_all()

# 비교
compare_results(results_a, results_b)
```

### 2. 모델 비교: GPT-4 vs GPT-3.5

```python
# config/llm_config.py 수정

# GPT-4 평가
evaluator_gpt4 = Text2SQLEvaluator(testset_path, db_url, model="gpt-4")
results_gpt4 = evaluator_gpt4.evaluate_all()

# GPT-3.5 평가
evaluator_gpt35 = Text2SQLEvaluator(testset_path, db_url, model="gpt-3.5-turbo")
results_gpt35 = evaluator_gpt35.evaluate_all()
```

### 3. RAG 유무 비교

```python
# RAG 있음
evaluator_with_rag = Text2SQLEvaluator(testset_path, db_url, use_rag=True)
results_with_rag = evaluator_with_rag.evaluate_all()

# RAG 없음
evaluator_no_rag = Text2SQLEvaluator(testset_path, db_url, use_rag=False)
results_no_rag = evaluator_no_rag.evaluate_all()
```

### 4. 오류 분석

```python
# 실패한 케이스만 필터링
failed_cases = results_df[results_df['execution_match'] == False]

# 오류 타입별 분류
error_types = {
    'syntax_error': [],
    'wrong_table': [],
    'wrong_join': [],
    'wrong_condition': []
}

for idx, row in failed_cases.iterrows():
    error_type = classify_error(row['error'], row['generated_sql'])
    error_types[error_type].append(row)

# 오류 패턴 분석
analyze_error_patterns(error_types)
```

### 5. 난이도별 세부 분석

```python
# 난이도별 성능 추이
for difficulty in ['초급', '중급', '고급']:
    diff_df = results_df[results_df['difficulty'] == difficulty]
    
    print(f"\n{difficulty} 난이도 분석:")
    print(f"  총 케이스: {len(diff_df)}개")
    print(f"  정확도: {diff_df['execution_match'].mean() * 100:.2f}%")
    print(f"  평균 생성 시간: {diff_df['generation_time'].mean():.2f}초")
    
    # 실패 케이스 분석
    failed = diff_df[diff_df['execution_match'] == False]
    if len(failed) > 0:
        print(f"  실패 케이스: {len(failed)}개")
        print(f"  주요 오류:")
        for error in failed['error'].value_counts().head(3).items():
            print(f"    - {error[0]}: {error[1]}건")
```

---

## 📈 성능 개선 전략

### 1. 프롬프트 엔지니어링

#### Before (기본)
```
질문: {question}
SQL을 생성하세요.
```

#### After (개선)
```
당신은 PostgreSQL 전문가입니다.
다음 질문에 대한 SQL 쿼리를 생성하세요.

데이터베이스 스키마:
- customer (customer_id, first_name, last_name, email, active)
- rental (rental_id, customer_id, inventory_id, rental_date, return_date)
- payment (payment_id, customer_id, amount, payment_date)
...

질문: {question}

주의사항:
1. 테이블명과 컬럼명을 정확히 사용하세요
2. 적절한 JOIN을 사용하세요
3. 집계 함수는 ROUND()로 소수점 2자리까지 표시하세요

SQL:
```

### 2. Few-shot Learning

```python
# 프롬프트에 예제 추가
examples = """
예제 1:
질문: 고객은 총 몇 명인가요?
SQL: SELECT COUNT(*) FROM customer;

예제 2:
질문: 가장 많이 대여된 영화는?
SQL: SELECT f.title FROM film f 
     JOIN inventory i ON f.film_id = i.film_id 
     JOIN rental r ON i.inventory_id = r.inventory_id 
     GROUP BY f.title 
     ORDER BY COUNT(r.rental_id) DESC 
     LIMIT 1;

이제 다음 질문에 답하세요:
질문: {question}
SQL:
"""
```

### 3. RAG 최적화

```python
# 관련 테이블만 검색
relevant_tables = retriever.get_relevant_tables(question, k=5)

# 스키마 정보 포함
schema_info = get_schema_info(relevant_tables)

# 프롬프트에 추가
prompt = f"""
관련 테이블:
{schema_info}

질문: {question}
SQL:
"""
```

### 4. 후처리 (Post-processing)

```python
def post_process_sql(generated_sql: str) -> str:
    """생성된 SQL 후처리"""
    
    # 1. 세미콜론 제거
    sql = generated_sql.rstrip(';')
    
    # 2. 불필요한 공백 제거
    sql = ' '.join(sql.split())
    
    # 3. 테이블 별칭 정규화
    sql = normalize_aliases(sql)
    
    # 4. 문법 검증
    if not validate_syntax(sql):
        sql = fix_common_errors(sql)
    
    return sql
```

---

## 🔄 지속적 개선 프로세스

### 1주차: 베이스라인 설정
1. 기본 프롬프트로 평가
2. 성능 지표 기록
3. 주요 오류 패턴 파악

### 2주차: 프롬프트 개선
1. 스키마 정보 추가
2. Few-shot 예제 추가
3. 재평가 및 비교

### 3주차: RAG 최적화
1. 임베딩 모델 변경
2. 검색 알고리즘 개선
3. 재평가 및 비교

### 4주차: 모델 업그레이드
1. GPT-4 등 더 강력한 모델 테스트
2. 비용 대비 성능 분석
3. 최종 모델 선택

---

## 📚 참고 자료

### 평가 메트릭 논문
- Spider: A Large-Scale Human-Labeled Dataset for Text-to-SQL Tasks
- WikiSQL: A Large-Scale Dataset for Text-to-SQL

### 프롬프트 엔지니어링
- OpenAI Best Practices for Prompt Engineering
- LangChain Documentation

### 데이터베이스 최적화
- PostgreSQL Performance Tuning
- SQL Query Optimization

---

## 🆘 문제 해결 (Troubleshooting)

### Q1: "테스트셋 파일을 찾을 수 없습니다"
```bash
# 테스트셋 생성 먼저 실행
python business_testset.py
```

### Q2: "데이터베이스 연결 오류"
```bash
# Docker 컨테이너 확인
docker ps

# 컨테이너 재시작
docker restart text2sql-db
```

### Q3: "LLM API 오류 (Rate Limit)"
```python
# evaluate_llm.py에서 sleep 시간 증가
time.sleep(1.0)  # 0.5 → 1.0으로 변경
```

### Q4: "메모리 부족"
```python
# 배치 단위로 평가
for i in range(0, len(df), 10):
    batch = df[i:i+10]
    results = evaluator.evaluate_batch(batch)
```

---

## ✅ 체크리스트

평가 전 확인사항:
- [ ] Docker 컨테이너 실행 중
- [ ] 테스트셋 생성 완료
- [ ] OpenAI API 키 설정
- [ ] 충분한 API 크레딧
- [ ] 결과 저장 폴더 존재

평가 후 확인사항:
- [ ] 결과 CSV 파일 생성
- [ ] 리포트 JSON 파일 생성
- [ ] 콘솔 출력 확인
- [ ] 주요 오류 패턴 분석
- [ ] 개선 방향 도출

---

**🎉 이제 Text2SQL LLM 성능을 체계적으로 평가할 수 있습니다!**
