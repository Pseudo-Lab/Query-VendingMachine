"""
testset.py 전용 평가 스크립트
정답 레이블(label)이 있는 테스트셋을 평가합니다.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# 설정
TESTSET_PATH = "experiments/dvdrental_testset.csv"

# Docker 내부에서 실행 시 text2sql-db 호스트명 사용
# 로컬에서 실행 시 127.0.0.1 사용
import os
if os.path.exists("/.dockerenv"):
    # Docker 컨테이너 내부
    DB_URL = "postgresql+psycopg2://user:password@text2sql-db:5432/dvdrental"
else:
    # 로컬 환경
    DB_URL = "postgresql+psycopg2://user:password@127.0.0.1:5432/dvdrental"

print("🔧 testset.py 평가 시작")
print(f"📂 테스트셋: {TESTSET_PATH}")
print(f"🗄️  데이터베이스: {DB_URL}\n")

# 1. 테스트셋 로드
print("📂 테스트셋 로드 중...")
df = pd.read_csv(TESTSET_PATH)
print(f"✅ {len(df)}개 케이스 로드 완료\n")

# 2. 데이터베이스 연결
print("🗄️  데이터베이스 연결 중...")
engine = create_engine(DB_URL)
print("✅ 연결 완료\n")

# 3. SQL 실행 및 결과 비교
print("=" * 80)
print("🧪 SQL 실행 테스트")
print("=" * 80)

results = []
success_count = 0
fail_count = 0
exact_match_count = 0  # Exact Match 카운트

for idx, row in df.iterrows():
    question = row['question']
    sql = row['sql']
    expected_label = row['label']
    
    print(f"\n[{idx+1}/{len(df)}] {question}")
    print(f"  SQL: {sql[:80]}...")
    print(f"  예상 결과: {expected_label}")
    
    try:
        # SQL 실행
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            
            # 결과 추출
            if len(rows) == 1 and len(rows[0]) == 1:
                actual_result = rows[0][0]
            elif len(rows) == 1:
                actual_result = rows[0][0]  # 첫 번째 컬럼
            else:
                actual_result = rows[0][0] if rows else None
            
            # Exact Match 체크 (완전 일치)
            exact_match = (str(expected_label) == str(actual_result))
            if exact_match:
                exact_match_count += 1
            
            # 결과 비교 (허용 오차 포함)
            # 숫자 비교 (소수점 오차 허용)
            if isinstance(expected_label, (int, float)) and isinstance(actual_result, (int, float)):
                match = abs(float(expected_label) - float(actual_result)) < 0.01
            # 문자열 비교
            elif isinstance(expected_label, str) and isinstance(actual_result, str):
                match = expected_label.strip().lower() == actual_result.strip().lower()
            else:
                match = str(expected_label) == str(actual_result)
            
            if match:
                em_mark = "✓" if exact_match else "≈"
                print(f"  ✅ 성공! 실제 결과: {actual_result} [{em_mark}]")
                success_count += 1
                results.append({
                    'question': question,
                    'sql': sql,
                    'expected': expected_label,
                    'actual': actual_result,
                    'match': True,
                    'exact_match': exact_match,
                    'error': None
                })
            else:
                print(f"  ❌ 불일치! 실제 결과: {actual_result}")
                fail_count += 1
                results.append({
                    'question': question,
                    'sql': sql,
                    'expected': expected_label,
                    'actual': actual_result,
                    'match': False,
                    'exact_match': False,
                    'error': f"Expected {expected_label}, got {actual_result}"
                })
    
    except Exception as e:
        print(f"  ❌ 오류: {str(e)[:100]}")
        fail_count += 1
        results.append({
            'question': question,
            'sql': sql,
            'expected': expected_label,
            'actual': None,
            'match': False,
            'exact_match': False,
            'error': str(e)
        })

# 4. 결과 저장 및 요약
print("\n" + "=" * 80)
print("📊 평가 결과 요약")
print("=" * 80)

# DataFrame 생성
results_df = pd.DataFrame(results)

# 정확도 계산
execution_accuracy = (success_count / len(df) * 100) if len(df) > 0 else 0
exact_match_accuracy = (exact_match_count / len(df) * 100) if len(df) > 0 else 0

print(f"\n📈 전체 통계:")
print(f"  • 총 테스트 케이스: {len(df)}개")
print(f"  • ✅ 성공 (Execution Accuracy): {success_count}개 ({execution_accuracy:.2f}%)")
print(f"  • ✓  완전 일치 (Exact Match): {exact_match_count}개 ({exact_match_accuracy:.2f}%)")
print(f"  • ❌ 실패: {fail_count}개 ({(fail_count/len(df)*100):.2f}%)")

print(f"\n📊 평가 지표:")
print(f"  • Execution Accuracy (EX): {execution_accuracy:.2f}%")
print(f"    → SQL 실행 결과가 정답과 일치 (허용 오차 포함)")
print(f"  • Exact Match (EM): {exact_match_accuracy:.2f}%")
print(f"    → 결과값이 완전히 동일 (문자열/숫자 완전 일치)")

# 실패 유형 분석
if fail_count > 0:
    print(f"\n🔍 실패 케이스 분석:")
    error_types = {}
    for result in results:
        if not result['match'] and result['error']:
            error_msg = result['error'][:50]
            error_types[error_msg] = error_types.get(error_msg, 0) + 1
    
    for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  • {error}... ({count}건)")

# 결과 CSV 저장
os.makedirs("experiments/evaluation", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"experiments/evaluation/testset_results_{timestamp}.csv"
results_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"\n💾 상세 결과 저장: {output_path}")

# 실패 케이스 출력 (최대 10개)
if fail_count > 0:
    print("\n" + "=" * 80)
    print(f"❌ 실패 케이스 상세 (총 {fail_count}개 중 최대 10개 표시)")
    print("=" * 80)
    
    failed = results_df[results_df['match'] == False].head(10)
    for idx, row in failed.iterrows():
        print(f"\n질문: {row['question']}")
        print(f"SQL: {row['sql'][:100]}...")
        print(f"예상: {row['expected']}")
        print(f"실제: {row['actual']}")
        if row['error']:
            print(f"오류: {row['error'][:100]}")

# 최종 요약
print("\n" + "=" * 80)
print("✅ 평가 완료!")
print("=" * 80)
print(f"\n📌 최종 요약:")
print(f"  • Execution Accuracy: {execution_accuracy:.2f}% ({success_count}/{len(df)})")
print(f"  • 상세 결과: {output_path}")
print()
