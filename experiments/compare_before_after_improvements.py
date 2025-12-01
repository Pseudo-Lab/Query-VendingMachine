"""
Compare accuracy BEFORE and AFTER prompt improvements
Uses the full testset.py dataset (90 questions)
"""
import pandas as pd
from chains.text_to_sql_chain import create_text_to_sql_chain
from utils import run_query
import time
from datetime import datetime

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

def evaluate_full_testset():
    """Evaluate all 90 questions from testset.py"""
    
    # Load testset
    df = pd.read_csv("experiments/dvdrental_testset.csv")
    total = len(df)
    
    print("=" * 80)
    print(f"Evaluating IMPROVED Chain on Full Testset ({total} questions)")
    print("=" * 80)
    print("\nImprovements applied:")
    print("  ✓ Added 7 critical few-shot examples (NOT IN, ::numeric, LIKE, IS NULL, etc.)")
    print("  ✓ Enhanced prompt with type casting rules")
    print("  ✓ Added NULL handling guidelines")
    print("  ✓ Added DISTINCT with JOINs rules")
    print("  ✓ Increased retrieval limit from 10 to 15")
    print("\n" + "=" * 80)
    
    chain = create_text_to_sql_chain()
    results = []
    correct = 0
    
    for idx, row in df.iterrows():
        q = row["question"]
        label = row["label"]
        
        print(f"\n[{idx+1}/{total}] {q[:60]}...")
        
        try:
            sql = chain.invoke(q)
            rows = run_query(sql, dvd=True)
            result = _scalar(rows)
            match = _match(label, result)
            
            if match:
                print(f"  ✅ PASS")
                correct += 1
            else:
                print(f"  ❌ FAIL - Expected: {label}, Got: {result}")
            
            results.append({
                "question": q,
                "expected": label,
                "sql": sql,
                "result": result,
                "match": match,
                "error": None
            })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)[:80]}")
            results.append({
                "question": q,
                "expected": label,
                "sql": None,
                "result": None,
                "match": False,
                "error": str(e)
            })
        
        time.sleep(0.2)  # Rate limiting
    
    # Calculate accuracy
    accuracy = (correct / total) * 100
    
    # Save results
    results_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"experiments/evaluation/improved_results_{timestamp}.csv"
    results_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    # Print summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nTotal Questions: {total}")
    print(f"Correct: {correct}")
    print(f"Failed: {total - correct}")
    print(f"\n🎯 IMPROVED ACCURACY: {accuracy:.2f}%")
    print(f"\n📊 Comparison:")
    print(f"   Before (baseline): ~31-34%")
    print(f"   After (improved):  {accuracy:.2f}%")
    print(f"   Improvement:       +{accuracy - 32:.2f}%")
    print(f"\n💾 Detailed results saved to: {output_path}")
    print("=" * 80)
    
    return accuracy, results_df

if __name__ == "__main__":
    evaluate_full_testset()
