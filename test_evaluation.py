"""
간단한 평가 테스트 스크립트
"""
import pandas as pd
from chains.text_to_sql_chain import create_text_to_sql_chain
from sqlalchemy import create_engine, text

# 설정
DB_URL = "postgresql://user:password@localhost:5432/dvdrental"
TESTSET_PATH = "experiments/business_testset.csv"

print("🔧 Text2SQL 평가 테스트 시작\n")

# 1. 테스트셋 로드
print("📂 테스트셋 로드 중...")
df = pd.read_csv(TESTSET_PATH)
print(f"✅ {len(df)}개 케이스 로드 완료\n")

# 2. 체인 생성
print("🔗 Text2SQL 체인 생성 중...")
chain = create_text_to_sql_chain()
print("✅ 체인 생성 완료\n")

# 3. 데이터베이스 연결
print("🗄️  데이터베이스 연결 중...")
engine = create_engine(DB_URL)
print("✅ 데이터베이스 연결 완료\n")

# 4. 첫 3개 케이스만 테스트
print("=" * 80)
print("🧪 테스트 시작 (첫 3개 케이스)")
print("=" * 80)

for idx in range(min(3, len(df))):
    row = df.iloc[idx]
    question = row['question']
    ground_truth_sql = row['sql']
    
    print(f"\n[{idx+1}/3] 질문: {question}")
    print(f"카테고리: {row['category']} | 난이도: {row['difficulty']}")
    
    try:
        # SQL 생성
        print("  🤖 SQL 생성 중...")
        generated_sql = chain.invoke({"question": question})
        print(f"  ✅ 생성 완료")
        print(f"  📝 생성된 SQL: {generated_sql[:100]}...")
        
        # 실행 테스트
        print("  🔍 SQL 실행 중...")
        with engine.connect() as conn:
            result = conn.execute(text(generated_sql))
            rows = result.fetchall()
            print(f"  ✅ 실행 성공! (결과: {len(rows)}행)")
            
            # 결과 출력
            if len(rows) == 1 and len(rows[0]) == 1:
                print(f"  📊 결과값: {rows[0][0]}")
        
    except Exception as e:
        print(f"  ❌ 오류 발생: {str(e)[:100]}")
    
    print("-" * 80)

print("\n✅ 테스트 완료!")
print("\n💡 전체 평가를 실행하려면:")
print("   python evaluate_llm.py")
