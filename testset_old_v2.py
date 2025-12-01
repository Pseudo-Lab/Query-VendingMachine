# 실무 중심의 Unique한 SQL 질의응답 테스트셋 (100개)
import pandas as pd

data = [
    # 1. 기본 통계 (10개)
    ["배우는 총 몇 명인가요?", "SELECT COUNT(*) FROM actor;", 200],
    ["고객은 총 몇 명인가요?", "SELECT COUNT(*) FROM customer;", 599],
    ["영화는 총 몇 편인가요?", "SELECT COUNT(*) FROM film;", 1000],
    ["전체 대여 건수는?", "SELECT COUNT(*) FROM rental;", 16044],
    ["전체 매출은 얼마인가요?", "SELECT ROUND(SUM(amount), 2) FROM payment;", 61312.04],
    ["활성 고객은 몇 명인가요?", "SELECT COUNT(*) FROM customer WHERE active = 1;", 584],
    ["반납되지 않은 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE return_date IS NULL;", 183],
    ["재고가 있는 영화는 몇 편인가요?", "SELECT COUNT(DISTINCT film_id) FROM inventory;", 958],
    ["카테고리는 총 몇 개인가요?", "SELECT COUNT(*) FROM category;", 16],
    ["Store 1과 Store 2의 고객 수 차이는?", "SELECT ABS((SELECT COUNT(*) FROM customer WHERE store_id = 1) - (SELECT COUNT(*) FROM customer WHERE store_id = 2));", 53],
    
    # 2. 고객 행동 분석 (15개)
    ["대여 횟수가 가장 많은 고객의 이름은?", "SELECT first_name || ' ' || last_name FROM customer ORDER BY (SELECT COUNT(*) FROM rental r WHERE r.customer_id = customer.customer_id) DESC LIMIT 1;", "Eleanor Hunt"],
    ["한 번도 대여하지 않은 고객은 몇 명인가요?", "SELECT COUNT(*) FROM customer WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM rental);", 0],
    ["가장 많은 금액을 지불한 고객의 총 결제액은?", "SELECT ROUND(SUM(amount), 2) FROM payment WHERE customer_id = (SELECT customer_id FROM payment GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 1);", 211.55],
    ["주말(토,일)에 대여한 고객 수는?", "SELECT COUNT(DISTINCT customer_id) FROM rental WHERE EXTRACT(DOW FROM rental_date) IN (0, 6);", 599],
    ["고객당 평균 대여 횟수는?", "SELECT ROUND(COUNT(*)::numeric / COUNT(DISTINCT customer_id), 2) FROM rental;", 26.79],
    ["이메일 도메인이 'sakilacustomer.org'인 고객 수는?", "SELECT COUNT(*) FROM customer WHERE email LIKE '%sakilacustomer.org';", 599],
    ["성과 이름이 같은 글자로 시작하는 고객 수는?", "SELECT COUNT(*) FROM customer WHERE LEFT(first_name, 1) = LEFT(last_name, 1);", 27],
    ["평균 이상으로 대여한 고객은 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT customer_id, COUNT(*) as cnt FROM rental GROUP BY customer_id HAVING COUNT(*) > (SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM rental GROUP BY customer_id) sub)) sub2;", 284],
    ["비활성 고객 비율은?", "SELECT ROUND((SELECT COUNT(*) FROM customer WHERE active = 0)::numeric / COUNT(*) * 100, 2) FROM customer;", 2.50],
    ["결제 없이 대여만 한 고객은 몇 명인가요?", "SELECT COUNT(DISTINCT customer_id) FROM rental WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM payment);", 0],
    ["가장 최근에 대여한 고객의 대여 날짜는?", "SELECT MAX(rental_date)::date FROM rental;", "2006-02-14"],
    ["한 달에 10회 이상 대여한 적이 있는 고객 수는?", "SELECT COUNT(DISTINCT customer_id) FROM (SELECT customer_id, EXTRACT(YEAR FROM rental_date) as year, EXTRACT(MONTH FROM rental_date) as month, COUNT(*) as cnt FROM rental GROUP BY customer_id, year, month HAVING COUNT(*) >= 10) sub;", 393],
    ["3개 이상의 카테고리 영화를 대여한 고객 수는?", "SELECT COUNT(*) FROM (SELECT r.customer_id FROM rental r JOIN inventory i ON r.inventory_id = i.inventory_id JOIN film_category fc ON i.film_id = fc.film_id GROUP BY r.customer_id HAVING COUNT(DISTINCT fc.category_id) >= 3) sub;", 599],
    ["가장 오래된 고객 계정은 언제 생성되었나요?", "SELECT MIN(create_date)::date FROM customer;", "2006-02-14"],
    ["Store 2에서 Store 1보다 고객이 몇 명 적나요?", "SELECT (SELECT COUNT(*) FROM customer WHERE store_id = 1) - (SELECT COUNT(*) FROM customer WHERE store_id = 2);", 53],
    
    # 3. 영화 콘텐츠 분석 (15개)
    ["가장 많은 배우가 출연한 영화의 배우 수는?", "SELECT COUNT(*) FROM film_actor WHERE film_id = (SELECT film_id FROM film_actor GROUP BY film_id ORDER BY COUNT(*) DESC LIMIT 1);", 15],
    ["배우가 한 명도 없는 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE film_id NOT IN (SELECT DISTINCT film_id FROM film_actor);", 0],
    ["평균보다 긴 영화 중 대여료가 평균보다 저렴한 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE length > (SELECT AVG(length) FROM film) AND rental_rate < (SELECT AVG(rental_rate) FROM film);", 162],
    ["'PG' 등급이면서 'Action' 카테고리인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id WHERE f.rating = 'PG' AND c.name = 'Action';", 30],
    ["제목이 'A'로 시작하는 영화 중 가장 긴 영화의 길이는?", "SELECT MAX(length) FROM film WHERE title LIKE 'A%';", 185],
    ["영화 길이의 표준편차는?", "SELECT ROUND(STDDEV(length)::numeric, 2) FROM film;", 40.43],
    ["대여료가 정확히 중간값인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_rate = (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rental_rate) FROM film);", 323],
    ["제목 길이가 가장 긴 영화의 글자 수는?", "SELECT MAX(LENGTH(title)) FROM film;", 27],
    ["'R' 등급 영화의 평균 길이가 'G' 등급보다 몇 분 더 긴가요?", "SELECT ROUND((SELECT AVG(length) FROM film WHERE rating = 'R') - (SELECT AVG(length) FROM film WHERE rating = 'G'), 2);", 3.42],
    ["가장 비싼 대여료와 가장 저렴한 대여료의 비율은?", "SELECT ROUND((SELECT MAX(rental_rate) FROM film) / (SELECT MIN(rental_rate) FROM film), 2);", 5.04],
    ["영화가 가장 많은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name ORDER BY COUNT(fc.film_id) DESC LIMIT 1;", "Sports"],
    ["영화가 가장 적은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name ORDER BY COUNT(fc.film_id) ASC LIMIT 1;", "Music"],
    ["평균 길이가 가장 긴 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id GROUP BY c.name ORDER BY AVG(f.length) DESC LIMIT 1;", "Sports"],
    ["평균 대여료가 가장 높은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id GROUP BY c.name ORDER BY AVG(f.rental_rate) DESC LIMIT 1;", "Games"],
    ["가장 많은 영화를 보유한 카테고리와 가장 적은 카테고리의 영화 수 차이는?", "SELECT (SELECT COUNT(*) FROM film_category WHERE category_id = (SELECT category_id FROM film_category GROUP BY category_id ORDER BY COUNT(*) DESC LIMIT 1)) - (SELECT COUNT(*) FROM film_category WHERE category_id = (SELECT category_id FROM film_category GROUP BY category_id ORDER BY COUNT(*) ASC LIMIT 1));", 18],
    
    # 4. 재고 및 운영 분석 (15개)
    ["재고가 가장 많은 영화의 재고 수는?", "SELECT COUNT(*) FROM inventory WHERE film_id = (SELECT film_id FROM inventory GROUP BY film_id ORDER BY COUNT(*) DESC LIMIT 1);", 8],
    ["재고가 1개뿐인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM (SELECT film_id FROM inventory GROUP BY film_id HAVING COUNT(*) = 1) sub;", 4],
    ["Store 1과 Store 2의 재고 차이는?", "SELECT ABS((SELECT COUNT(*) FROM inventory WHERE store_id = 1) - (SELECT COUNT(*) FROM inventory WHERE store_id = 2));", 1],
    ["대여 중인 재고의 비율은?", "SELECT ROUND((SELECT COUNT(*) FROM rental WHERE return_date IS NULL)::numeric / (SELECT COUNT(*) FROM inventory) * 100, 2);", 3.99],
    ["한 번도 대여되지 않은 재고는 몇 개인가요?", "SELECT COUNT(*) FROM inventory WHERE inventory_id NOT IN (SELECT DISTINCT inventory_id FROM rental);", 0],
    ["평균 이상으로 대여된 영화는 몇 편인가요?", "SELECT COUNT(*) FROM (SELECT i.film_id, COUNT(*) as cnt FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY i.film_id HAVING COUNT(*) > (SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM inventory i2 JOIN rental r2 ON i2.inventory_id = r2.inventory_id GROUP BY i2.film_id) sub)) sub2;", 477],
    ["재고가 없는 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE film_id NOT IN (SELECT DISTINCT film_id FROM inventory);", 42],
    ["대여가 한 번도 이루어지지 않은 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f WHERE NOT EXISTS (SELECT 1 FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id WHERE i.film_id = f.film_id);", 42],
    ["가장 많이 대여된 영화의 제목은?", "SELECT f.title FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY COUNT(r.rental_id) DESC LIMIT 1;", "Bucket Brotherhood"],
    ["가장 많이 대여된 영화의 대여 횟수는?", "SELECT COUNT(*) FROM rental r JOIN inventory i ON r.inventory_id = i.inventory_id WHERE i.film_id = (SELECT i2.film_id FROM inventory i2 JOIN rental r2 ON i2.inventory_id = r2.inventory_id GROUP BY i2.film_id ORDER BY COUNT(*) DESC LIMIT 1);", 34],
    ["대여 중인 영화는 몇 편인가요?", "SELECT COUNT(DISTINCT i.film_id) FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id WHERE r.return_date IS NULL;", 169],
    ["반납된 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE return_date IS NOT NULL;", 15861],
    ["평균 대여 기간은 며칠인가요?", "SELECT ROUND(AVG(EXTRACT(DAY FROM (return_date - rental_date)))) FROM rental WHERE return_date IS NOT NULL;", 5],
    ["가장 많이 대여된 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY c.name ORDER BY COUNT(r.rental_id) DESC LIMIT 1;", "Sports"],
    ["Store 1의 평균 재고 수는?", "SELECT ROUND(COUNT(*)::numeric / COUNT(DISTINCT film_id), 2) FROM inventory WHERE store_id = 1;", 2.40],
    
    # 5. 매출 및 결제 분석 (15개) - 더 다양하게
    ["고객의 평균 결제 금액은 얼마인가요?", "SELECT ROUND(AVG(amount), 2) FROM payment;", 4.20],
    ["얼마나 결제를 해야 전체 유저 중에서 상위 10%에 해당할까?", "SELECT ROUND(percentile_disc(0.9) WITHIN GROUP (ORDER BY total_amount), 2) FROM (SELECT customer_id, SUM(amount) AS total_amount FROM payment GROUP BY customer_id) AS customer_totals;", 134.69],
    ["결제가 가장 많이 일어난 시간대는?", "SELECT EXTRACT(HOUR FROM payment_date)::int FROM payment GROUP BY EXTRACT(HOUR FROM payment_date) ORDER BY COUNT(*) DESC LIMIT 1;", 13],
    ["일별 평균 매출은?", "SELECT ROUND(AVG(daily_revenue), 2) FROM (SELECT DATE(payment_date) as date, SUM(amount) as daily_revenue FROM payment GROUP BY DATE(payment_date)) sub;", 4200.82],
    ["가장 매출이 높았던 날의 매출액은?", "SELECT ROUND(MAX(daily_revenue), 2) FROM (SELECT DATE(payment_date) as date, SUM(amount) as daily_revenue FROM payment GROUP BY DATE(payment_date)) sub;", 6056.09],
    ["결제 금액의 표준편차는?", "SELECT ROUND(STDDEV(amount)::numeric, 2) FROM payment;", 1.91],
    ["스태프 1이 처리한 총 매출은?", "SELECT ROUND(SUM(amount), 2) FROM payment WHERE staff_id = 1;", 33927.04],
    ["스태프 2가 처리한 총 매출은?", "SELECT ROUND(SUM(amount), 2) FROM payment WHERE staff_id = 2;", 27385.00],
    ["가장 비싼 단일 결제 금액은?", "SELECT MAX(amount) FROM payment;", 11.99],
    ["가장 저렴한 단일 결제 금액은?", "SELECT MIN(amount) FROM payment;", 0.00],
    ["0.99달러 결제 건수는?", "SELECT COUNT(*) FROM payment WHERE amount = 0.99;", 580],
    ["4.99달러 이상 결제 건수는?", "SELECT COUNT(*) FROM payment WHERE amount >= 4.99;", 5638],
    ["고객당 평균 총 결제액은?", "SELECT ROUND(AVG(total), 2) FROM (SELECT customer_id, SUM(amount) as total FROM payment GROUP BY customer_id) sub;", 102.37],
    ["2월에 발생한 매출은?", "SELECT ROUND(SUM(amount), 2) FROM payment WHERE EXTRACT(MONTH FROM payment_date) = 2;", 9631.88],
    ["7월에 발생한 매출은?", "SELECT ROUND(SUM(amount), 2) FROM payment WHERE EXTRACT(MONTH FROM payment_date) = 7;", 28373.89],
    
    # 6. 배우 및 출연 분석 (10개) - 더 다양하게
    ["출연 영화가 가장 많은 배우의 출연 영화 수는?", "SELECT COUNT(*) FROM film_actor WHERE actor_id = (SELECT actor_id FROM film_actor GROUP BY actor_id ORDER BY COUNT(*) DESC LIMIT 1);", 42],
    ["배우당 평균 출연 영화 수는?", "SELECT ROUND(COUNT(*)::numeric / COUNT(DISTINCT actor_id), 2) FROM film_actor;", 27.34],
    ["'Action' 카테고리에 출연한 배우는 몇 명인가요?", "SELECT COUNT(DISTINCT fa.actor_id) FROM film_actor fa JOIN film_category fc ON fa.film_id = fc.film_id JOIN category c ON fc.category_id = c.category_id WHERE c.name = 'Action';", 180],
    ["가장 다양한 카테고리에 출연한 배우의 카테고리 수는?", "SELECT COUNT(DISTINCT fc.category_id) FROM film_actor fa JOIN film_category fc ON fa.film_id = fc.film_id WHERE fa.actor_id = (SELECT fa2.actor_id FROM film_actor fa2 JOIN film_category fc2 ON fa2.film_id = fc2.film_id GROUP BY fa2.actor_id ORDER BY COUNT(DISTINCT fc2.category_id) DESC LIMIT 1);", 16],
    ["'R' 등급 영화에만 출연한 배우는 몇 명인가요?", "SELECT COUNT(DISTINCT fa.actor_id) FROM film_actor fa JOIN film f ON fa.film_id = f.film_id WHERE f.rating = 'R' AND fa.actor_id NOT IN (SELECT fa2.actor_id FROM film_actor fa2 JOIN film f2 ON fa2.film_id = f2.film_id WHERE f2.rating != 'R');", 0],
    ["가장 긴 영화에 출연한 배우 수는?", "SELECT COUNT(*) FROM film_actor WHERE film_id = (SELECT film_id FROM film ORDER BY length DESC LIMIT 1);", 10],
    ["가장 비싼 대여료 영화에 출연한 배우 수는?", "SELECT COUNT(*) FROM film_actor WHERE film_id IN (SELECT film_id FROM film WHERE rental_rate = (SELECT MAX(rental_rate) FROM film));", 3360],
    ["평균 이상의 영화에 출연한 배우는 몇 명인가요?", "SELECT COUNT(DISTINCT actor_id) FROM film_actor WHERE actor_id IN (SELECT actor_id FROM film_actor GROUP BY actor_id HAVING COUNT(*) > (SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM film_actor GROUP BY actor_id) sub));", 109],
    ["단 1편의 영화에만 출연한 배우는 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT actor_id FROM film_actor GROUP BY actor_id HAVING COUNT(*) = 1) sub;", 0],
    ["가장 많이 대여된 영화에 출연한 배우 수는?", "SELECT COUNT(*) FROM film_actor WHERE film_id = (SELECT i.film_id FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY i.film_id ORDER BY COUNT(*) DESC LIMIT 1);", 12],
    
    # 7. 시간 및 트렌드 분석 (10개) - 더 다양하게
    ["2005년에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(YEAR FROM rental_date) = 2005;", 15862],
    ["평일(월-금)에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(DOW FROM rental_date) BETWEEN 1 AND 5;", 11475],
    ["주말(토-일)에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(DOW FROM rental_date) IN (0, 6);", 4569],
    ["가장 대여가 많았던 날의 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE DATE(rental_date) = (SELECT DATE(rental_date) FROM rental GROUP BY DATE(rental_date) ORDER BY COUNT(*) DESC LIMIT 1);", 335],
    ["가장 대여가 적었던 날의 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE DATE(rental_date) = (SELECT DATE(rental_date) FROM rental GROUP BY DATE(rental_date) ORDER BY COUNT(*) ASC LIMIT 1);", 1],
    ["오전(0-11시)에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(HOUR FROM rental_date) < 12;", 2649],
    ["오후(12-23시)에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(HOUR FROM rental_date) >= 12;", 13395],
    ["월요일에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(DOW FROM rental_date) = 1;", 2298],
    ["토요일에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(DOW FROM rental_date) = 6;", 2328],
    ["평균 영화 길이는?", "SELECT ROUND(AVG(length), 2) FROM film;", 115.27]
]

if __name__=="__main__":
    df = pd.DataFrame(data, columns=["question", "sql", "label"])
    csv_path = "experiments/dvdrental_testset.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"✅ 테스트셋 생성 완료: {csv_path}")
    print(f"📊 총 {len(df)}개의 테스트 케이스")
    print(f"\n💡 평가 방법:")
    print(f"   docker exec text2sql-web python /app/evaluate_testset.py")
