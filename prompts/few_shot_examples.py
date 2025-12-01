"""
Few-shot 예제 모듈

복잡한 SQL 패턴을 학습하기 위한 예제들을 제공합니다.
"""

FEW_SHOT_EXAMPLES = [
    {
        "question": "배우는 총 몇 명인가요?",
        "sql": "SELECT COUNT(*) FROM actor;",
        "explanation": "단일 테이블에서 COUNT 집계"
    },
    {
        "question": "가장 많은 금액을 지불한 고객의 총 결제액은?",
        "sql": "SELECT ROUND(SUM(amount), 2) FROM payment WHERE customer_id = (SELECT customer_id FROM payment GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 1);",
        "explanation": "서브쿼리를 사용한 집계 및 필터링"
    },
    {
        "question": "'PG' 등급이면서 'Action' 카테고리인 영화는 몇 편인가요?",
        "sql": "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id WHERE f.rating = 'PG' AND c.name = 'Action';",
        "explanation": "다중 JOIN과 WHERE 조건"
    },
    {
        "question": "평균보다 긴 영화 중 대여료가 평균보다 저렴한 영화는 몇 편인가요?",
        "sql": "SELECT COUNT(*) FROM film WHERE length > (SELECT AVG(length) FROM film) AND rental_rate < (SELECT AVG(rental_rate) FROM film);",
        "explanation": "다중 서브쿼리를 사용한 비교"
    },
    {
        "question": "영화 길이의 표준편차는?",
        "sql": "SELECT ROUND(STDDEV(length)::numeric, 2) FROM film;",
        "explanation": "통계 함수 사용 (STDDEV)"
    },
    {
        "question": "가장 많이 대여된 영화의 제목은?",
        "sql": "SELECT f.title FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY COUNT(r.rental_id) DESC LIMIT 1;",
        "explanation": "다중 JOIN, GROUP BY, ORDER BY, LIMIT"
    },
    {
        "question": "주말(토,일)에 대여한 고객 수는?",
        "sql": "SELECT COUNT(DISTINCT customer_id) FROM rental WHERE EXTRACT(DOW FROM rental_date) IN (0, 6);",
        "explanation": "날짜 함수 EXTRACT와 IN 연산자"
    },
    {
        "question": "평균 이상으로 대여한 고객은 몇 명인가요?",
        "sql": "SELECT COUNT(*) FROM (SELECT customer_id, COUNT(*) as cnt FROM rental GROUP BY customer_id HAVING COUNT(*) > (SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM rental GROUP BY customer_id) sub)) sub2;",
        "explanation": "중첩 서브쿼리와 HAVING 절"
    },
    {
        "question": "3개 이상의 카테고리 영화를 대여한 고객 수는?",
        "sql": "SELECT COUNT(*) FROM (SELECT r.customer_id FROM rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN film_category fc ON i.film_id = fc.film_id GROUP BY r.customer_id HAVING COUNT(DISTINCT fc.category_id) >= 3) sub;",
        "explanation": "다중 JOIN과 DISTINCT COUNT를 사용한 집계"
    },
    {
        "question": "가장 비싼 대여료와 가장 저렴한 대여료의 비율은?",
        "sql": "SELECT ROUND((SELECT MAX(rental_rate) FROM film) / (SELECT MIN(rental_rate) FROM film), 2);",
        "explanation": "서브쿼리를 사용한 계산"
    },
    {
        "question": "배우가 한 명도 없는 영화는 몇 편인가요?",
        "sql": "SELECT COUNT(*) FROM film WHERE film_id NOT IN (SELECT DISTINCT film_id FROM film_actor);",
        "explanation": "NOT IN with DISTINCT for exclusion"
    },
    {
        "question": "비활성 고객 비율은?",
        "sql": "SELECT ROUND((SELECT COUNT(*) FROM customer WHERE active = 0)::numeric / COUNT(*) * 100, 2) FROM customer;",
        "explanation": "Type casting ::numeric for accurate division"
    },
    {
        "question": "제목이 'A'로 시작하는 영화 중 가장 긴 영화의 길이는?",
        "sql": "SELECT MAX(length) FROM film WHERE title LIKE 'A%';",
        "explanation": "LIKE pattern with aggregation"
    },
    {
        "question": "반납되지 않은 대여 건수는?",
        "sql": "SELECT COUNT(*) FROM rental WHERE return_date IS NULL;",
        "explanation": "NULL check with IS NULL"
    },
    {
        "question": "가장 최근에 대여한 고객의 대여 날짜는?",
        "sql": "SELECT MAX(rental_date)::date FROM rental;",
        "explanation": "Date type casting"
    },
    {
        "question": "Store 1과 Store 2의 고객 수 차이는?",
        "sql": "SELECT ABS((SELECT COUNT(*) FROM customer WHERE store_id = 1) - (SELECT COUNT(*) FROM customer WHERE store_id = 2));",
        "explanation": "ABS for absolute value"
    }
]


def format_few_shot_examples() -> str:
    """
    Few-shot 예제를 프롬프트에 포함할 수 있는 형식으로 변환
    
    Returns:
        str: 포맷팅된 예제 문자열
    """
    examples_text = []
    for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        examples_text.append(
            f"Example {i}:\n"
            f"Question: {example['question']}\n"
            f"SQL: {example['sql']}\n"
        )
    return "\n".join(examples_text)
