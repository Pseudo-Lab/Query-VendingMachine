"""
Quick test to demonstrate accuracy improvement from prompt enhancements
Runs a sample of testset queries to show before/after comparison
"""
import pandas as pd
from chains.text_to_sql_chain import create_text_to_sql_chain
from utils import run_query
import time

def _scalar(rows):
    if not rows:
        return None
    r = rows[0]
    if isinstance(r, dict):
        return list(r.values())[0] if r else None
    return r[0] if len(r) > 0 else None

def _match(expected, actual):
    try:
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return abs(float(expected) - float(actual)) < 0.01
        return str(expected).strip().lower() == str(actual).strip().lower()
    except Exception:
        return str(expected) == str(actual)

def test_sample():
    """Test a representative sample of queries"""
    df = pd.read_csv("experiments/dvdrental_testset.csv")
    
    # Focus on queries that were failing before
    critical_indices = [
        26,  # 배우가 한 명도 없는 영화 (NOT IN with DISTINCT)
        27,  # 평균보다 긴 영화 (multiple subqueries)
        28,  # 'PG' 등급이면서 'Action' (JOIN)
        29,  # 제목이 'A'로 시작 (LIKE)
        30,  # 영화 길이의 표준편차 (STDDEV with ::numeric)
        31,  # 대여료가 정확히 중간값 (PERCENTILE_CONT)
        18,  # 비활성 고객 비율 (division with ::numeric)
        12,  # 반납되지 않은 대여 (IS NULL)
        20,  # 가장 최근에 대여한 고객 (::date casting)
    ]
    
    sample_df = df.iloc[critical_indices]
    
    chain = create_text_to_sql_chain()
    results = []
    correct = 0
    
    print("=" * 80)
    print("Testing Critical Queries with Improvements")
    print("=" * 80)
    
    for idx, row in sample_df.iterrows():
        q = row["question"]
        label = row["label"]
        
        print(f"\n[{idx+1}] {q}")
        print(f"Expected: {label}")
        
        try:
            sql = chain.invoke(q)
            print(f"Generated SQL: {sql[:100]}...")
            
            rows = run_query(sql, dvd=True)
            result = _scalar(rows)
            match = _match(label, result)
            
            if match:
                print(f"✅ PASS - Result: {result}")
                correct += 1
            else:
                print(f"❌ FAIL - Got: {result}")
                
            results.append({
                "question": q,
                "expected": label,
                "sql": sql,
                "result": result,
                "match": match
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:100]}")
            results.append({
                "question": q,
                "expected": label,
                "sql": None,
                "result": None,
                "match": False
            })
        
        time.sleep(0.3)
    
    accuracy = (correct / len(sample_df)) * 100
    
    print("\n" + "=" * 80)
    print(f"Sample Accuracy: {accuracy:.2f}% ({correct}/{len(sample_df)})")
    print("=" * 80)
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv("experiments/evaluation/improvement_test.csv", index=False, encoding="utf-8-sig")
    print(f"\nResults saved to: experiments/evaluation/improvement_test.csv")
    
    return accuracy

if __name__ == "__main__":
    test_sample()
