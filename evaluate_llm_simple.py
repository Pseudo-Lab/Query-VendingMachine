"""
간단한 LLM Text2SQL 평가 스크립트
business_testset.csv를 사용하여 LLM이 생성한 SQL을 평가합니다.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import time

# LangChain imports
from chains.text_to_sql_chain import create_text_to_sql_chain

# 설정
TESTSET_PATH = "experiments/business_testset.csv"

# Docker 내부에서 실행 시 text2sql-db 호스트명 사용
if os.path.exists("/.dockerenv"):
    DB_URL = "postgresql+psycopg2://user:password@text2sql-db:5432/dvdrental"
else:
    DB_URL = "postgresql+psycopg2://user:password@127.0.0.1:5432/dvdrental"

print("🔧 LLM Text2SQL 평가 시작")
print(f"📂 테스트셋: {TESTSET_PATH}")
print(f"🗄️  데이터베이스: {DB_URL}\n")

# 1. 테스트셋 로드
print("📂 테스트셋 로드 중...")
df = pd.read_csv(TESTSET_PATH)
print(f"✅ {len(df)}개 케이스 로드 완료\n")

# 2. LLM 체인 생성
print("🤖 LLM 체인 생성 중...")
try:
    chain = create_text_to_sql_chain()
    print("✅ 체인 생성 완료\n")
except Exception as e:
    print(f"❌ 체인 생성 실패: {e}")
    exit(1)

# 3. 데이터베이스 연결
print("🗄️  데이터베이스 연결 중...")
engine = create_engine(DB_URL)
print("✅ 연결 완료\n")

# 4. 평가 실행
print("=" * 80)
print("🧪 LLM SQL 생성 및 실행 테스트")
print("=" * 80)

results = []
success_count = 0
fail_count = 0

for idx, row in df.iterrows():
    question = row['question']
    ground_truth_sql = row['sql']
    category = row['category']
    difficulty = row['difficulty']
    
    print(f"\n[{idx+1}/{len(df)}] {question}")
    print(f"  카테고리: {category} | 난이도: {difficulty}")
    
    try:
        # LLM으로 SQL 생성
        print("  🤖 LLM이 SQL 생성 중...")
        start_time = time.time()
        generated_sql = chain.invoke({"question": question})
        generation_time = time.time() - start_time
        
        print(f"  ✅ 생성 완료 ({generation_time:.2f}초)")
        print(f"  📝 생성된 SQL: {generated_sql[:80]}...")
        
        # 정답 SQL 실행
        with engine.connect() as conn:
            gt_result = conn.execute(text(ground_truth_sql))
            gt_rows = gt_result.fetchall()
            gt_value = gt_rows[0][0] if gt_rows and len(gt_rows[0]) > 0 else None
        
        # 생성된 SQL 실행
        try:
            with engine.connect() as conn:
                gen_result = conn.execute(text(generated_sql))
                gen_rows = gen_result.fetchall()
                gen_value = gen_rows[0][0] if gen_rows and len(gen_rows[0]) > 0 else None
            
            # 결과 비교
            if str(gt_value) == str(gen_value):
                print(f"  ✅ 성공! 결과 일치: {gen_value}")
                success_count += 1
                match = True
            else:
                print(f"  ❌ 불일치! 정답: {gt_value}, 생성: {gen_value}")
                fail_count += 1
                match = False
            
            results.append({
                'question': question,
                'category': category,
                'difficulty': difficulty,
                'ground_truth_sql': ground_truth_sql,
                'generated_sql': generated_sql,
                'expected': gt_value,
                'actual': gen_value,
                'match': match,
                'generation_time': generation_time,
                'error': None
            })
            
        except Exception as e:
            print(f"  ❌ 생성된 SQL 실행 오류: {str(e)[:100]}")
            fail_count += 1
            results.append({
                'question': question,
                'category': category,
                'difficulty': difficulty,
                'ground_truth_sql': ground_truth_sql,
                'generated_sql': generated_sql,
                'expected': gt_value,
                'actual': None,
                'match': False,
                'generation_time': generation_time,
                'error': str(e)
            })
    
    except Exception as e:
        print(f"  ❌ SQL 생성 오류: {str(e)[:100]}")
        fail_count += 1
        results.append({
            'question': question,
            'category': category,
            'difficulty': difficulty,
            'ground_truth_sql': ground_truth_sql,
            'generated_sql': None,
            'expected': None,
            'actual': None,
            'match': False,
            'generation_time': 0,
            'error': str(e)
        })
    
    # API Rate Limit 방지
    time.sleep(0.5)

# 5. 결과 저장 및 출력
print("\n" + "=" * 80)
print("📊 평가 결과")
print("=" * 80)

accuracy = (success_count / len(df) * 100) if len(df) > 0 else 0

print(f"\n✅ 성공: {success_count}개")
print(f"❌ 실패: {fail_count}개")
print(f"📈 정확도: {accuracy:.2f}%")

# 카테고리별 성능
print("\n📊 카테고리별 성능:")
results_df = pd.DataFrame(results)
for category in results_df['category'].unique():
    cat_df = results_df[results_df['category'] == category]
    cat_accuracy = (cat_df['match'].sum() / len(cat_df) * 100)
    print(f"  • {category:25s}: {cat_accuracy:5.2f}% ({cat_df['match'].sum()}/{len(cat_df)})")

# 난이도별 성능
print("\n📊 난이도별 성능:")
for difficulty in ['초급', '중급', '고급']:
    diff_df = results_df[results_df['difficulty'] == difficulty]
    if len(diff_df) > 0:
        diff_accuracy = (diff_df['match'].sum() / len(diff_df) * 100)
        print(f"  • {difficulty:10s}: {diff_accuracy:5.2f}% ({diff_df['match'].sum()}/{len(diff_df)})")

# 결과 CSV 저장
os.makedirs("experiments/evaluation", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"experiments/evaluation/llm_results_{timestamp}.csv"
results_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"\n✅ 결과 저장: {output_path}")

# 실패 케이스 출력
if fail_count > 0:
    print("\n" + "=" * 80)
    print("❌ 실패 케이스 상세 (최대 10개)")
    print("=" * 80)
    
    failed = results_df[results_df['match'] == False].head(10)
    for idx, row in failed.iterrows():
        print(f"\n질문: {row['question']}")
        print(f"카테고리: {row['category']} | 난이도: {row['difficulty']}")
        if row['generated_sql']:
            print(f"생성 SQL: {row['generated_sql'][:100]}...")
        print(f"예상: {row['expected']}")
        print(f"실제: {row['actual']}")
        if row['error']:
            print(f"오류: {row['error'][:100]}")

print("\n✅ 평가 완료!")
