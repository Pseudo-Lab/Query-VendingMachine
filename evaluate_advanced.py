"""
고급 Text2SQL 평가 스크립트
학계 표준 평가 지표 추가 구현

참고 논문:
- Spider: Yu et al., 2018
- BIRD: Li et al., 2023
- Test-Suite Accuracy: Zhong et al., 2020
"""

import pandas as pd
import sqlparse
from sqlalchemy import create_engine, text
from typing import Dict, List, Tuple, Set
import re
from collections import defaultdict


class AdvancedText2SQLEvaluator:
    """학계 표준 평가 지표를 포함한 고급 평가 클래스"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(db_url)
    
    # ==================== 1. Component Matching (Spider 방식) ====================
    
    def extract_sql_components(self, sql: str) -> Dict[str, Set]:
        """
        SQL을 구성 요소로 분해
        Spider 논문의 Component Matching 방식
        """
        sql = sql.lower().strip()
        
        components = {
            'select': set(),
            'from': set(),
            'where': set(),
            'group_by': set(),
            'order_by': set(),
            'keywords': set()
        }
        
        # SELECT 절 추출
        select_match = re.search(r'select\s+(.*?)\s+from', sql, re.IGNORECASE)
        if select_match:
            select_clause = select_match.group(1)
            components['select'] = set(re.findall(r'\w+', select_clause))
        
        # FROM 절 추출 (테이블명)
        from_match = re.search(r'from\s+(.*?)(?:\s+where|\s+group|\s+order|\s+limit|$)', sql, re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1)
            # 테이블명만 추출 (JOIN 제외)
            tables = re.findall(r'(\w+)(?:\s+as\s+\w+|\s+\w+)?', from_clause)
            components['from'] = set(tables)
        
        # WHERE 절 추출
        where_match = re.search(r'where\s+(.*?)(?:\s+group|\s+order|\s+limit|$)', sql, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            components['where'] = set(re.findall(r'\w+', where_clause))
        
        # GROUP BY 절 추출
        if 'group by' in sql:
            components['keywords'].add('group_by')
            group_match = re.search(r'group\s+by\s+(.*?)(?:\s+having|\s+order|\s+limit|$)', sql, re.IGNORECASE)
            if group_match:
                components['group_by'] = set(re.findall(r'\w+', group_match.group(1)))
        
        # ORDER BY 절 추출
        if 'order by' in sql:
            components['keywords'].add('order_by')
            order_match = re.search(r'order\s+by\s+(.*?)(?:\s+limit|$)', sql, re.IGNORECASE)
            if order_match:
                components['order_by'] = set(re.findall(r'\w+', order_match.group(1)))
        
        # 집계 함수
        agg_functions = ['count', 'sum', 'avg', 'min', 'max']
        for func in agg_functions:
            if func in sql:
                components['keywords'].add(func)
        
        # JOIN
        if 'join' in sql:
            components['keywords'].add('join')
        
        # DISTINCT
        if 'distinct' in sql:
            components['keywords'].add('distinct')
        
        # LIMIT
        if 'limit' in sql:
            components['keywords'].add('limit')
        
        return components
    
    def component_matching_score(self, generated_sql: str, ground_truth_sql: str) -> Dict[str, float]:
        """
        Component Matching Score 계산
        각 SQL 구성 요소별 정확도 측정
        """
        gen_comp = self.extract_sql_components(generated_sql)
        gt_comp = self.extract_sql_components(ground_truth_sql)
        
        scores = {}
        
        for component in ['select', 'from', 'where', 'group_by', 'order_by', 'keywords']:
            gen_set = gen_comp[component]
            gt_set = gt_comp[component]
            
            if len(gt_set) == 0:
                scores[component] = 1.0 if len(gen_set) == 0 else 0.0
            else:
                # F1 Score 계산
                intersection = len(gen_set & gt_set)
                precision = intersection / len(gen_set) if len(gen_set) > 0 else 0
                recall = intersection / len(gt_set) if len(gt_set) > 0 else 0
                
                if precision + recall > 0:
                    f1 = 2 * precision * recall / (precision + recall)
                else:
                    f1 = 0.0
                
                scores[component] = f1
        
        # 전체 평균
        scores['overall'] = sum(scores.values()) / len(scores)
        
        return scores
    
    # ==================== 2. Test-Suite Accuracy (Zhong et al., 2020) ====================
    
    def generate_test_suite(self, sql: str, num_tests: int = 5) -> List[Dict]:
        """
        Test Suite 생성
        여러 데이터베이스 상태에서 테스트
        """
        test_suite = []
        
        try:
            with self.engine.connect() as conn:
                for i in range(num_tests):
                    # 원본 쿼리 실행
                    result = conn.execute(text(sql))
                    rows = result.fetchall()
                    
                    test_suite.append({
                        'test_id': i,
                        'result': rows,
                        'row_count': len(rows)
                    })
        except Exception as e:
            return []
        
        return test_suite
    
    def test_suite_accuracy(self, generated_sql: str, ground_truth_sql: str) -> float:
        """
        Test Suite Accuracy 계산
        여러 테스트 케이스에서 일치 비율
        """
        gen_suite = self.generate_test_suite(generated_sql)
        gt_suite = self.generate_test_suite(ground_truth_sql)
        
        if not gen_suite or not gt_suite:
            return 0.0
        
        matches = sum(1 for g, t in zip(gen_suite, gt_suite) if g['result'] == t['result'])
        return matches / len(gt_suite)
    
    # ==================== 3. Partial Credit (부분 점수) ====================
    
    def calculate_partial_credit(self, generated_sql: str, ground_truth_sql: str) -> Dict[str, float]:
        """
        부분 점수 계산
        완전히 틀려도 부분적으로 맞으면 점수 부여
        """
        scores = {
            'table_selection': 0.0,  # 올바른 테이블 선택
            'column_selection': 0.0,  # 올바른 컬럼 선택
            'join_correctness': 0.0,  # JOIN 정확성
            'filter_correctness': 0.0,  # WHERE 조건 정확성
            'aggregation': 0.0,  # 집계 함수 사용
            'grouping': 0.0,  # GROUP BY 정확성
            'ordering': 0.0,  # ORDER BY 정확성
        }
        
        gen_comp = self.extract_sql_components(generated_sql)
        gt_comp = self.extract_sql_components(ground_truth_sql)
        
        # 1. 테이블 선택 점수
        if gen_comp['from'] and gt_comp['from']:
            scores['table_selection'] = len(gen_comp['from'] & gt_comp['from']) / len(gt_comp['from'])
        
        # 2. 컬럼 선택 점수
        if gen_comp['select'] and gt_comp['select']:
            scores['column_selection'] = len(gen_comp['select'] & gt_comp['select']) / len(gt_comp['select'])
        
        # 3. JOIN 점수
        if 'join' in gt_comp['keywords']:
            scores['join_correctness'] = 1.0 if 'join' in gen_comp['keywords'] else 0.0
        else:
            scores['join_correctness'] = 1.0 if 'join' not in gen_comp['keywords'] else 0.5
        
        # 4. 필터 점수
        if gen_comp['where'] and gt_comp['where']:
            scores['filter_correctness'] = len(gen_comp['where'] & gt_comp['where']) / len(gt_comp['where'])
        elif not gt_comp['where'] and not gen_comp['where']:
            scores['filter_correctness'] = 1.0
        
        # 5. 집계 함수 점수
        agg_funcs = {'count', 'sum', 'avg', 'min', 'max'}
        gen_agg = gen_comp['keywords'] & agg_funcs
        gt_agg = gt_comp['keywords'] & agg_funcs
        if gt_agg:
            scores['aggregation'] = 1.0 if gen_agg == gt_agg else 0.0
        else:
            scores['aggregation'] = 1.0 if not gen_agg else 0.5
        
        # 6. GROUP BY 점수
        if 'group_by' in gt_comp['keywords']:
            scores['grouping'] = 1.0 if 'group_by' in gen_comp['keywords'] else 0.0
        else:
            scores['grouping'] = 1.0
        
        # 7. ORDER BY 점수
        if 'order_by' in gt_comp['keywords']:
            scores['ordering'] = 1.0 if 'order_by' in gen_comp['keywords'] else 0.0
        else:
            scores['ordering'] = 1.0
        
        # 전체 평균
        scores['total'] = sum(scores.values()) / len(scores)
        
        return scores
    
    # ==================== 4. SQL 복잡도 분석 ====================
    
    def analyze_sql_complexity(self, sql: str) -> Dict[str, any]:
        """
        SQL 복잡도 분석
        Spider 논문의 난이도 분류 기준
        """
        sql_lower = sql.lower()
        
        complexity = {
            'num_tables': 0,
            'num_joins': 0,
            'num_conditions': 0,
            'has_subquery': False,
            'has_aggregation': False,
            'has_group_by': False,
            'has_order_by': False,
            'has_nested_query': False,
            'difficulty': 'easy'
        }
        
        # 테이블 수
        from_match = re.search(r'from\s+(.*?)(?:\s+where|\s+group|\s+order|\s+limit|$)', sql_lower)
        if from_match:
            tables = re.findall(r'\b\w+\b', from_match.group(1))
            complexity['num_tables'] = len([t for t in tables if t not in ['join', 'on', 'as', 'left', 'right', 'inner', 'outer']])
        
        # JOIN 수
        complexity['num_joins'] = sql_lower.count('join')
        
        # 조건 수
        if 'where' in sql_lower:
            where_match = re.search(r'where\s+(.*?)(?:\s+group|\s+order|\s+limit|$)', sql_lower)
            if where_match:
                complexity['num_conditions'] = where_match.group(1).count('and') + where_match.group(1).count('or') + 1
        
        # 서브쿼리
        complexity['has_subquery'] = '(' in sql and 'select' in sql[sql.index('('):]
        
        # 집계 함수
        complexity['has_aggregation'] = any(func in sql_lower for func in ['count', 'sum', 'avg', 'min', 'max'])
        
        # GROUP BY
        complexity['has_group_by'] = 'group by' in sql_lower
        
        # ORDER BY
        complexity['has_order_by'] = 'order by' in sql_lower
        
        # 중첩 쿼리
        complexity['has_nested_query'] = sql_lower.count('select') > 1
        
        # 난이도 분류 (Spider 기준)
        if complexity['has_nested_query'] or complexity['num_joins'] >= 3:
            complexity['difficulty'] = 'extra_hard'
        elif complexity['num_joins'] >= 2 or complexity['has_subquery']:
            complexity['difficulty'] = 'hard'
        elif complexity['num_joins'] == 1 or complexity['has_aggregation']:
            complexity['difficulty'] = 'medium'
        else:
            complexity['difficulty'] = 'easy'
        
        return complexity
    
    # ==================== 5. 종합 평가 ====================
    
    def comprehensive_evaluation(self, question: str, generated_sql: str, ground_truth_sql: str) -> Dict:
        """종합 평가 수행"""
        
        result = {
            'question': question,
            'generated_sql': generated_sql,
            'ground_truth_sql': ground_truth_sql,
        }
        
        # 1. Component Matching
        result['component_matching'] = self.component_matching_score(generated_sql, ground_truth_sql)
        
        # 2. Partial Credit
        result['partial_credit'] = self.calculate_partial_credit(generated_sql, ground_truth_sql)
        
        # 3. SQL 복잡도
        result['complexity'] = self.analyze_sql_complexity(ground_truth_sql)
        
        # 4. Test Suite Accuracy (선택적)
        # result['test_suite_accuracy'] = self.test_suite_accuracy(generated_sql, ground_truth_sql)
        
        return result


# ==================== 6. 오류 분류 ====================

class ErrorClassifier:
    """SQL 생성 오류 자동 분류"""
    
    ERROR_TYPES = {
        'syntax_error': ['syntax error', 'invalid syntax', 'parse error'],
        'table_not_found': ['table', 'does not exist', 'relation'],
        'column_not_found': ['column', 'does not exist'],
        'join_error': ['join', 'on clause'],
        'aggregation_error': ['group by', 'aggregate'],
        'type_error': ['type', 'cannot be', 'invalid type'],
        'permission_error': ['permission', 'denied'],
    }
    
    @staticmethod
    def classify_error(error_message: str) -> str:
        """오류 메시지 분류"""
        if not error_message:
            return 'no_error'
        
        error_lower = error_message.lower()
        
        for error_type, keywords in ErrorClassifier.ERROR_TYPES.items():
            if any(keyword in error_lower for keyword in keywords):
                return error_type
        
        return 'unknown_error'
    
    @staticmethod
    def analyze_error_patterns(results_df: pd.DataFrame) -> Dict:
        """오류 패턴 분석"""
        failed_cases = results_df[results_df['execution_match'] == False]
        
        error_analysis = {
            'total_errors': len(failed_cases),
            'error_distribution': defaultdict(int),
            'by_difficulty': defaultdict(lambda: defaultdict(int)),
            'by_category': defaultdict(lambda: defaultdict(int)),
        }
        
        for idx, row in failed_cases.iterrows():
            error_type = ErrorClassifier.classify_error(row.get('error', ''))
            error_analysis['error_distribution'][error_type] += 1
            
            if 'difficulty' in row:
                error_analysis['by_difficulty'][row['difficulty']][error_type] += 1
            
            if 'category' in row:
                error_analysis['by_category'][row['category']][error_type] += 1
        
        return dict(error_analysis)


# ==================== 사용 예제 ====================

def example_usage():
    """사용 예제"""
    
    DB_URL = "postgresql://user:password@localhost:5432/dvdrental"
    
    evaluator = AdvancedText2SQLEvaluator(DB_URL)
    
    # 예제 SQL
    question = "가장 많이 대여된 영화는?"
    generated_sql = "SELECT f.title FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY COUNT(*) DESC LIMIT 1;"
    ground_truth_sql = "SELECT f.title FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY COUNT(r.rental_id) DESC LIMIT 1;"
    
    # 종합 평가
    result = evaluator.comprehensive_evaluation(question, generated_sql, ground_truth_sql)
    
    print("=" * 80)
    print("고급 평가 결과")
    print("=" * 80)
    print(f"\n질문: {question}")
    print(f"\n📊 Component Matching Scores:")
    for component, score in result['component_matching'].items():
        print(f"  {component:15s}: {score:.2%}")
    
    print(f"\n📊 Partial Credit Scores:")
    for aspect, score in result['partial_credit'].items():
        print(f"  {aspect:20s}: {score:.2%}")
    
    print(f"\n📊 SQL Complexity:")
    for key, value in result['complexity'].items():
        print(f"  {key:20s}: {value}")


if __name__ == "__main__":
    example_usage()
