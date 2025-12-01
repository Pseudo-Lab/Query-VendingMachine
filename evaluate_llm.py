"""
Text2SQL LLM 성능 평가 스크립트

이 스크립트는 다음을 수행합니다:
1. 테스트셋의 질문을 LLM에 입력
2. 생성된 SQL과 정답 SQL 비교
3. 실행 결과 비교
4. 성능 지표 계산 및 리포트 생성
"""

import pandas as pd
import time
from datetime import datetime
from sqlalchemy import create_engine, text
from typing import Dict, List, Tuple
import json
import os
from dotenv import load_dotenv

# 프로젝트 모듈 import
from chains.text_to_sql_chain import create_text_to_sql_chain
from config.llm_config import get_llm

load_dotenv()


class Text2SQLEvaluator:
    """Text2SQL 모델 성능 평가 클래스"""
    
    def __init__(self, testset_path: str, db_url: str):
        """
        Args:
            testset_path: 테스트셋 CSV 파일 경로
            db_url: 데이터베이스 연결 URL
        """
        self.testset_path = testset_path
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.chain = create_text_to_sql_chain()
        
        # 결과 저장
        self.results = []
        
    def load_testset(self) -> pd.DataFrame:
        """테스트셋 로드"""
        df = pd.read_csv(self.testset_path)
        print(f"✅ 테스트셋 로드 완료: {len(df)}개 케이스")
        return df
    
    def execute_sql(self, sql: str) -> Tuple[bool, any]:
        """
        SQL 실행
        
        Returns:
            (성공 여부, 결과 또는 에러 메시지)
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                
                # 단일 값 반환
                if len(rows) == 1 and len(rows[0]) == 1:
                    return True, rows[0][0]
                # 여러 행 반환
                return True, rows
        except Exception as e:
            return False, str(e)
    
    def normalize_sql(self, sql: str) -> str:
        """SQL 정규화 (비교를 위해)"""
        # 공백, 줄바꿈 정규화
        sql = ' '.join(sql.split())
        # 세미콜론 제거
        sql = sql.rstrip(';')
        # 소문자 변환
        sql = sql.lower()
        return sql
    
    def compare_results(self, result1, result2) -> bool:
        """실행 결과 비교"""
        try:
            # 타입 변환
            if isinstance(result1, (int, float)) and isinstance(result2, (int, float)):
                return abs(float(result1) - float(result2)) < 0.01
            
            # 문자열 비교
            if isinstance(result1, str) and isinstance(result2, str):
                return result1.strip().lower() == result2.strip().lower()
            
            # 리스트 비교
            if isinstance(result1, list) and isinstance(result2, list):
                return result1 == result2
            
            return result1 == result2
        except:
            return False
    
    def evaluate_single(self, question: str, ground_truth_sql: str, category: str, difficulty: str) -> Dict:
        """단일 케이스 평가"""
        start_time = time.time()
        
        result = {
            'question': question,
            'category': category,
            'difficulty': difficulty,
            'ground_truth_sql': ground_truth_sql,
            'generated_sql': None,
            'exact_match': False,
            'execution_match': False,
            'valid_sql': False,
            'error': None,
            'generation_time': 0,
            'ground_truth_result': None,
            'generated_result': None
        }
        
        try:
            # 1. LLM으로 SQL 생성
            generated_sql = self.chain.invoke({"question": question})
            result['generated_sql'] = generated_sql
            result['generation_time'] = time.time() - start_time
            
            # 2. Exact Match 체크
            if self.normalize_sql(generated_sql) == self.normalize_sql(ground_truth_sql):
                result['exact_match'] = True
            
            # 3. 정답 SQL 실행
            gt_success, gt_result = self.execute_sql(ground_truth_sql)
            result['ground_truth_result'] = str(gt_result)
            
            # 4. 생성된 SQL 실행
            gen_success, gen_result = self.execute_sql(generated_sql)
            
            if gen_success:
                result['valid_sql'] = True
                result['generated_result'] = str(gen_result)
                
                # 5. Execution Match 체크
                if gt_success and self.compare_results(gt_result, gen_result):
                    result['execution_match'] = True
            else:
                result['error'] = gen_result
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def evaluate_all(self, limit: int = None) -> pd.DataFrame:
        """전체 테스트셋 평가"""
        df = self.load_testset()
        
        if limit:
            df = df.head(limit)
            print(f"⚠️  제한: {limit}개 케이스만 평가")
        
        print(f"\n🚀 평가 시작: {len(df)}개 케이스")
        print("=" * 80)
        
        for idx, row in df.iterrows():
            print(f"\n[{idx+1}/{len(df)}] {row['question']}")
            
            result = self.evaluate_single(
                question=row['question'],
                ground_truth_sql=row['sql'],
                category=row['category'],
                difficulty=row['difficulty']
            )
            
            self.results.append(result)
            
            # 결과 출력
            status = "✅" if result['execution_match'] else "❌"
            print(f"{status} Exact Match: {result['exact_match']}, "
                  f"Execution Match: {result['execution_match']}, "
                  f"Valid SQL: {result['valid_sql']}")
            
            if result['error']:
                print(f"   ⚠️  Error: {result['error'][:100]}")
            
            # Rate limit 방지
            time.sleep(0.5)
        
        return pd.DataFrame(self.results)
    
    def generate_report(self, results_df: pd.DataFrame) -> Dict:
        """성능 리포트 생성"""
        total = len(results_df)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_cases': int(total),  # numpy int64 -> Python int
            'metrics': {
                'exact_match': {
                    'count': int(results_df['exact_match'].sum()),
                    'percentage': round(float(results_df['exact_match'].sum() / total * 100), 2)
                },
                'execution_accuracy': {
                    'count': int(results_df['execution_match'].sum()),
                    'percentage': round(float(results_df['execution_match'].sum() / total * 100), 2)
                },
                'valid_sql': {
                    'count': int(results_df['valid_sql'].sum()),
                    'percentage': round(float(results_df['valid_sql'].sum() / total * 100), 2)
                }
            },
            'avg_generation_time': round(float(results_df['generation_time'].mean()), 2),
            'by_category': {},
            'by_difficulty': {}
        }
        
        # 카테고리별 성능
        for category in results_df['category'].unique():
            cat_df = results_df[results_df['category'] == category]
            report['by_category'][str(category)] = {
                'total': int(len(cat_df)),
                'execution_accuracy': round(float(cat_df['execution_match'].sum() / len(cat_df) * 100), 2)
            }
        
        # 난이도별 성능
        for difficulty in results_df['difficulty'].unique():
            diff_df = results_df[results_df['difficulty'] == difficulty]
            report['by_difficulty'][str(difficulty)] = {
                'total': int(len(diff_df)),
                'execution_accuracy': round(float(diff_df['execution_match'].sum() / len(diff_df) * 100), 2)
            }
        
        return report
    
    def save_results(self, results_df: pd.DataFrame, report: Dict, output_dir: str = "experiments/evaluation"):
        """결과 저장"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 상세 결과 CSV
        csv_path = f"{output_dir}/results_{timestamp}.csv"
        results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 상세 결과 저장: {csv_path}")
        
        # 2. 리포트 JSON
        json_path = f"{output_dir}/report_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"✅ 리포트 저장: {json_path}")
        
        # 3. 콘솔 출력
        self.print_report(report)
    
    def print_report(self, report: Dict):
        """리포트 콘솔 출력"""
        print("\n" + "=" * 80)
        print("📊 Text2SQL LLM 성능 평가 리포트")
        print("=" * 80)
        
        print(f"\n📅 평가 시간: {report['timestamp']}")
        print(f"📝 총 테스트 케이스: {report['total_cases']}개")
        
        print("\n🎯 전체 성능 지표:")
        print(f"  • Exact Match (EM):        {report['metrics']['exact_match']['count']:3d}개 ({report['metrics']['exact_match']['percentage']:5.2f}%)")
        print(f"  • Execution Accuracy (EX): {report['metrics']['execution_accuracy']['count']:3d}개 ({report['metrics']['execution_accuracy']['percentage']:5.2f}%)")
        print(f"  • Valid SQL (VS):          {report['metrics']['valid_sql']['count']:3d}개 ({report['metrics']['valid_sql']['percentage']:5.2f}%)")
        print(f"  • 평균 생성 시간:          {report['avg_generation_time']:.2f}초")
        
        print("\n📂 카테고리별 성능:")
        for category, stats in report['by_category'].items():
            print(f"  • {category:25s}: {stats['execution_accuracy']:5.2f}% ({stats['total']}개)")
        
        print("\n⭐ 난이도별 성능:")
        for difficulty, stats in report['by_difficulty'].items():
            print(f"  • {difficulty:10s}: {stats['execution_accuracy']:5.2f}% ({stats['total']}개)")
        
        print("\n" + "=" * 80)


def main():
    """메인 실행 함수"""
    
    # 설정
    # business_testset.csv (51개) 또는 dvdrental_testset.csv (30개) 선택
    # TESTSET_PATH = "experiments/dvdrental_testset.csv"  # testset.py 결과 (category 컬럼 없음)
    TESTSET_PATH = "experiments/business_testset.csv"  # business_testset.py 결과 (category, difficulty 있음)
    
    DB_URL = "postgresql://user:password@text2sql-db:5432/dvdrental"
    
    # 로컬에서 실행할 경우
    if not os.path.exists("/.dockerenv"):
        DB_URL = "postgresql://user:password@localhost:5432/dvdrental"
    
    print("🔧 Text2SQL LLM 성능 평가 시작")
    print(f"📂 테스트셋: {TESTSET_PATH}")
    print(f"🗄️  데이터베이스: {DB_URL}")
    
    # 평가 실행
    evaluator = Text2SQLEvaluator(TESTSET_PATH, DB_URL)
    
    # 전체 평가 (또는 limit=10으로 제한)
    results_df = evaluator.evaluate_all(limit=None)  # limit=10으로 테스트 가능
    
    # 리포트 생성 및 저장
    report = evaluator.generate_report(results_df)
    evaluator.save_results(results_df, report)
    
    print("\n✅ 평가 완료!")


if __name__ == "__main__":
    main()
