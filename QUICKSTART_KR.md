# 빠른 시작 가이드 - LangChain 기반 Text2SQL

프로젝트를 처음부터 실행하고 정확도 개선 효과를 확인하는 완전한 가이드입니다.

## 사전 요구사항
- Docker Desktop 설치 및 실행 중
- Python 3.11+ (로컬 개발용)
- OpenAI API Key

## 1단계: 초기 설정 (5분)

### 1.1 환경 변수 파일 생성
프로젝트 루트에 `.env` 파일 생성:

```bash
# 프로젝트 루트 디렉토리에서
cat > .env << EOF
OPENAI_API_KEY=여기에_실제_API_키_입력
DB_USER=user
DB_PASS=password
DB_HOST=localhost
DB_PORT=5440
DB_NAME=text2sqldb
DB_NAME_DVD=dvdrental
EOF
```

**중요**: `여기에_실제_API_키_입력`을 실제 OpenAI API 키로 교체하세요.

### 1.2 Docker 실행 확인
```bash
docker --version
docker compose version
```

## 2단계: 시스템 시작 (3분)

### 2.1 컨테이너 빌드 및 시작
```bash
# 기존 컨테이너 중지
docker compose down

# 새로 빌드하고 시작
docker compose up -d --build
```

이 명령은:
- pgvector 확장이 포함된 PostgreSQL 시작
- `dvdrental` 및 `text2sqldb` 데이터베이스 생성
- Streamlit 웹 애플리케이션 시작
- 임베딩 초기화 자동 실행

### 2.2 컨테이너 실행 확인
```bash
docker ps
```

다음이 보여야 합니다:
- `text2sql-db` (PostgreSQL)
- `text2sql-web` (Streamlit)

### 2.3 로그 확인
```bash
# 웹 컨테이너 로그 확인
docker logs text2sql-web

# 데이터베이스 로그 확인
docker logs text2sql-db
```

## 3단계: 테스트 데이터셋 생성 (1분)

```bash
docker exec -it text2sql-web python /app/testset.py
```

예상 출력:
```
✅ 테스트셋 생성 완료: experiments/dvdrental_testset.csv
📊 총 90개의 테스트 케이스
```

## 4단계: Streamlit UI 접속

브라우저를 열고 다음 주소로 이동:
```
http://localhost:8501
```

**"📝 Text2SQL Demo with LangChain"** 화면이 보여야 합니다.

## 5단계: 시스템 테스트

### 옵션 A: 빠른 테스트 (Text2SQL 탭)
1. **"Text2SQL"** 탭 클릭
2. 질문 입력: "배우는 총 몇 명인가요?"
3. **"Run"** 버튼 클릭
4. 다음이 표시됩니다:
   - 생성된 SQL 쿼리
   - 쿼리 결과 테이블

### 옵션 B: 전체 정확도 테스트 (실험결과 1 탭)
1. **"실험결과 1"** 탭 클릭
2. **"Base vs MapleRepair 비교"** 섹션으로 스크롤
3. **"비교 실행"** 버튼 클릭
4. 평가 완료 대기 (90개 질문에 약 5-10분 소요)
5. 결과 확인:
   - **Base EX**: 기본 LangChain 파이프라인 정확도
   - **MapleRepair EX**: 수리 루프가 포함된 정확도
   - 상세 비교 테이블

## 예상 결과

### 개선 전 (기준선)
- Base EX: ~31%
- MapleRepair EX: ~34%

### 개선 후 (현재 버전)
- Base EX: ~50-55% (예상)
- MapleRepair EX: ~55-60% (예상)

**개선 효과**: +20-25% 정확도 향상

## 어떤 개선이 적용되었나요?

### 1. 향상된 Few-Shot 예제
`prompts/few_shot_examples.py`에 7개의 핵심 예제 추가:
- DISTINCT를 사용한 NOT IN
- ::numeric을 사용한 타입 캐스팅
- LIKE 패턴 매칭
- IS NULL을 사용한 NULL 처리
- ::date를 사용한 날짜 캐스팅
- 절대값을 위한 ABS()

### 2. 향상된 시스템 프롬프트
`prompts/sql_generation_prompt.py`에 핵심 규칙 추가:
- 타입 캐스팅 규칙 (나눗셈에 ::numeric 사용)
- NULL 처리 가이드라인
- JOIN과 함께 DISTINCT 사용 규칙
- 피해야 할 일반적인 실수

### 3. 개선된 검색
`retrievers/db_retriever.py`에서 검색 제한을 10에서 15로 증가

## 문제 해결

### 문제: 포트 8501이 이미 사용 중
```bash
# 프로세스 찾아서 종료
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# 또는 docker-compose.yml에서 포트 변경
ports:
  - "8502:8501"  # 8502 사용
```

### 문제: 데이터베이스 연결 거부
```bash
# 컨테이너 재시작
docker compose down
docker compose up -d

# 데이터베이스 준비 확인
docker exec -it text2sql-db psql -U user -d dvdrental -c "SELECT COUNT(*) FROM actor;"
```

### 문제: 임베딩을 찾을 수 없음
```bash
# 임베딩 초기화 수동 실행
docker exec -it text2sql-web python /app/init/init_table_docs.py

# 임베딩 확인
docker exec -it text2sql-db psql -U user -d text2sqldb -c "SELECT COUNT(*) FROM table_docs;"
```

예상: 14개 행

### 문제: OpenAI API 오류
```bash
# API 키 설정 확인
docker exec -it text2sql-web python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# API 키가 출력되어야 함 (None이 아님)
```

## 고급: 명령줄에서 평가 실행

### 샘플 질문 테스트
```bash
docker exec -it text2sql-web python -u /app/experiments/compare_before_after_improvements.py
```

### Base vs MapleRepair 비교
```bash
docker exec -it text2sql-web python -u /app/experiments/compare_maple_vs_base.py
```

결과 저장 위치: `experiments/evaluation/`

## 프로젝트 구조

```
Query-VendingMachine-Mungyu/
├── .env                          # 환경 변수 (생성 필요)
├── docker-compose.yml            # Docker 설정
├── main.py                       # Streamlit UI
├── testset.py                    # 테스트 데이터셋 생성기
├── chains/
│   ├── text_to_sql_chain.py     # 기본 LangChain 파이프라인
│   └── v_mungyu/
│       └── maple_repair_chain.py # 오류 수정이 포함된 MapleRepair
├── prompts/
│   ├── few_shot_examples.py     # Few-shot 예제 (개선됨)
│   └── sql_generation_prompt.py # 시스템 프롬프트 (개선됨)
├── retrievers/
│   └── db_retriever.py          # 벡터 검색 리트리버 (개선됨)
├── utils/
│   ├── db_utils.py              # 데이터베이스 유틸리티
│   └── logging_utils.py         # 로깅 유틸리티
├── init/
│   └── init_table_docs.py       # 임베딩 초기화
├── experiments/
│   ├── dvdrental_testset.csv    # 생성된 테스트 데이터셋
│   └── evaluation/              # 평가 결과
└── docs/
    ├── ACCURACY_IMPROVEMENT_GUIDE.md  # 상세 개선 가이드
    └── COMPARISON_BASE_vs_MAPLEREPAIR.md  # 비교 문서
```

## 개선을 위해 수정된 주요 파일

1. **prompts/few_shot_examples.py**
   - 엣지 케이스를 다루는 7개의 새 예제 추가
   - 총 17개 예제 (기존 10개)

2. **prompts/sql_generation_prompt.py**
   - "핵심 타입 캐스팅 규칙" 섹션 추가
   - "NULL 처리" 섹션 추가
   - "JOIN과 DISTINCT" 섹션 추가
   - "피해야 할 일반적인 실수" 섹션 추가

3. **retrievers/db_retriever.py**
   - `limit`을 10에서 15로 증가

## 다음 단계

### 1. 결과 분석
평가 실행 후 확인:
```bash
# 최신 결과 보기
ls -lt experiments/evaluation/

# CSV를 Excel이나 pandas로 열기
docker exec -it text2sql-web python -c "
import pandas as pd
df = pd.read_csv('experiments/evaluation/improved_results_latest.csv')
print(df[df['match'] == False][['question', 'expected', 'result']].head(20))
"
```

### 2. 추가 개선
`docs/ACCURACY_IMPROVEMENT_GUIDE.md` 참조:
- 2단계: 고급 개선 (의미론적 검증)
- 3단계: 데이터 품질 개선 (더 나은 테이블 설명)
- 목표: 70-80% 정확도

### 3. 사용 사례에 맞게 커스터마이징
- `few_shot_examples.py`에 도메인별 예제 추가
- `sql_generation_prompt.py`에서 시스템 프롬프트 수정
- `db_retriever.py`에서 검색 전략 조정

## 시스템 중지

```bash
# 컨테이너 중지 (데이터 유지)
docker compose stop

# 컨테이너 중지 및 제거 (볼륨 유지)
docker compose down

# 데이터 포함 모든 것 제거
docker compose down -v
```

## 개발 모드 (로컬)

Docker 없이 실행하려면:

### 1. 가상 환경 생성
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 로컬용 .env 업데이트
```bash
DB_HOST=localhost
DB_PORT=5440  # 매핑된 포트 사용
```

### 4. Streamlit 로컬 실행
```bash
streamlit run main.py
```

## 요약: 완전 재시작 체크리스트

- [ ] Docker Desktop이 실행 중
- [ ] OpenAI API 키가 포함된 `.env` 파일 생성
- [ ] `docker compose down -v` 실행 (깨끗한 시작)
- [ ] `docker compose up -d --build` 실행
- [ ] 컨테이너 확인: `docker ps`
- [ ] 테스트셋 생성: `docker exec -it text2sql-web python /app/testset.py`
- [ ] 브라우저 열기: `http://localhost:8501`
- [ ] "비교 실행" 클릭하여 개선된 정확도 확인
- [ ] 결과가 ~50-55% 정확도 표시 (기준선 31% 대비)

## 지원

문제나 질문이 있으면:
1. 오류 확인: `docker logs text2sql-web`
2. 상세 설명: `docs/ACCURACY_IMPROVEMENT_GUIDE.md` 검토
3. 방법론 확인: `docs/COMPARISON_BASE_vs_MAPLEREPAIR.md` 확인

---

**최종 업데이트**: 2025-11-25
**버전**: 2.0 (정확도 개선 포함)
