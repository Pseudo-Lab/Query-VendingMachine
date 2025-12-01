# 단일 정답에 대한 SQL 질의응답 테스트셋 생성 코드
import pandas as pd

data = [
    # 기본 통계 (10개)
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

    # 중급
    ["가장 많은 배우가 출연한 영화의 제목은?", "SELECT f.title FROM film f JOIN film_actor fa ON f.film_id = fa.film_id GROUP BY f.title ORDER BY COUNT(fa.actor_id) DESC LIMIT 1;", "Lambs Cincinatti"],
    ["영화의 평균 대여료는 얼마인가요?", "SELECT ROUND(AVG(rental_rate), 2) FROM film;", 2.98],
    ["영화의 최대 대여료는 얼마인가요?", "SELECT MAX(rental_rate) FROM film;", 4.99],
    ["영화의 최소 대여료는 얼마인가요?", "SELECT MIN(rental_rate) FROM film;", 0.99],
    ["‘Comedy’ 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Comedy';", 58],
    ["영화가 가장 많은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name ORDER BY COUNT(fc.film_id) DESC LIMIT 1;", "Sports"],
    ["대여 횟수가 가장 많은 고객의 이름은?", "SELECT first_name || ' ' || last_name FROM customer ORDER BY (SELECT COUNT(*) FROM rental r WHERE r.customer_id = customer.customer_id) DESC LIMIT 1;", "ELEANOR HUNT"],
    ["스태프는 몇 명인가요?", "SELECT COUNT(*) FROM staff;", 2],
    ["스토어는 몇 개 있나요?", "SELECT COUNT(*) FROM store;", 2],
    ["‘Action’ 카테고리 영화들의 평균 길이는 얼마인가요?", "SELECT ROUND(AVG(f.length), 2) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Action';", 111.61],

    # 고급
    ["평균보다 긴 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE length > (SELECT AVG(length) FROM film);", 507],
    ["가장 많이 대여된 영화의 제목은?", "SELECT f.title FROM film f JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY f.title ORDER BY COUNT(r.rental_id) DESC LIMIT 1;", "Bucket Brotherhood"],
    ["가장 많이 대여된 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id JOIN inventory i ON f.film_id = i.film_id JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY c.name ORDER BY COUNT(r.rental_id) DESC LIMIT 1;", "Sports"],
    ["가장 많이 대여한 고객의 총 대여 횟수는?", "SELECT COUNT(*) FROM rental r WHERE r.customer_id = (SELECT customer_id FROM rental GROUP BY customer_id ORDER BY COUNT(*) DESC LIMIT 1);", 46],
    ["고객의 평균 결제 금액은 얼마인가요?", "SELECT ROUND(AVG(amount), 2) FROM payment;", 4.20],
    ["얼마나 결제를 해야 전체 유저 중에서 상위 10%에 해당할까?", "SELECT percentile_disc(0.9) WITHIN GROUP (ORDER BY total_amount) AS top_10_percent_threshold FROM (SELECT customer_id, SUM(amount) AS total_amount FROM payment GROUP BY customer_id ) AS customer_totals;;", "134.69"],
    ["결제가 가장 많이 일어난 시간대는?", "SELECT EXTRACT(HOUR FROM payment_date)::int AS hour_of_day, COUNT(*) AS payment_count FROM payment GROUP BY hour_of_day ORDER BY payment_count DESC LIMIT 1;", "13"],
    ["대여가 한 번도 이루어지지 않은 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f WHERE NOT EXISTS (SELECT 1 FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id WHERE i.film_id = f.film_id);", 42],
    ["평균 대여료가 가장 높은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id GROUP BY c.name ORDER BY AVG(f.rental_rate) DESC LIMIT 1;", "Games"],
    ["평균 길이가 가장 짧은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id GROUP BY c.name ORDER BY AVG(f.length) ASC LIMIT 1;", "Sci-Fi"],

    # 추가 질문 (50개)
    # 초급 추가
    ["주소는 총 몇 개인가요?", "SELECT COUNT(*) FROM address;", 603],
    ["카테고리는 총 몇 개인가요?", "SELECT COUNT(*) FROM category;", 16],
    ["전체 재고 수는?", "SELECT COUNT(*) FROM inventory;", 4581],
    ["전체 대여 건수는?", "SELECT COUNT(*) FROM rental;", 16044],
    ["전체 결제 건수는?", "SELECT COUNT(*) FROM payment;", 14596],
    ["'PG-13' 등급 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rating = 'PG-13';", 223],
    ["'R' 등급 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rating = 'R';", 195],
    ["대여료가 2.99인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_rate = 2.99;", 323],
    ["대여료가 4.99인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_rate = 4.99;", 336],
    ["영화 길이가 100분 이상인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE length >= 100;", 535],

    # 중급 추가
    ["'Drama' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Drama';", 62],
    ["'Horror' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Horror';", 56],
    ["영화가 가장 적은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id GROUP BY c.name ORDER BY COUNT(fc.film_id) ASC LIMIT 1;", "Music"],
    ["평균 길이가 가장 긴 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id GROUP BY c.name ORDER BY AVG(f.length) DESC LIMIT 1;", "Sports"],
    ["대여 기간이 7일인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_duration = 7;", 203],
    ["대여 기간이 3일인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_duration = 3;", 203],
    ["영화 제목에 'LOVE'가 포함된 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE title LIKE '%LOVE%';", 5],
    ["영화 제목에 'DRAGON'이 포함된 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE title LIKE '%DRAGON%';", 3],
    ["출연 영화가 가장 많은 배우의 출연 영화 수는?", "SELECT COUNT(*) FROM film_actor WHERE actor_id = (SELECT actor_id FROM film_actor GROUP BY actor_id ORDER BY COUNT(*) DESC LIMIT 1);", 42],
    ["출연 영화가 10편 이상인 배우는 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT actor_id FROM film_actor GROUP BY actor_id HAVING COUNT(*) >= 10) sub;", 198],

    # 고급 추가
    ["가장 많이 대여된 영화의 대여 횟수는?", "SELECT COUNT(*) FROM rental r JOIN inventory i ON r.inventory_id = i.inventory_id WHERE i.film_id = (SELECT i2.film_id FROM inventory i2 JOIN rental r2 ON i2.inventory_id = r2.inventory_id GROUP BY i2.film_id ORDER BY COUNT(*) DESC LIMIT 1);", 34],
    ["대여 횟수가 30회 이상인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM (SELECT i.film_id FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id GROUP BY i.film_id HAVING COUNT(*) >= 30) sub;", 237],
    ["평균보다 짧은 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE length < (SELECT AVG(length) FROM film);", 511],
    ["평균보다 비싼 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_rate > (SELECT AVG(rental_rate) FROM film);", 658],
    ["평균보다 저렴한 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_rate < (SELECT AVG(rental_rate) FROM film);", 342],
    ["대여 횟수가 20회 이상인 고객은 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT customer_id FROM rental GROUP BY customer_id HAVING COUNT(*) >= 20) sub;", 520],
    ["대여 횟수가 30회 이상인 고객은 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT customer_id FROM rental GROUP BY customer_id HAVING COUNT(*) >= 30) sub;", 273],
    ["대여 횟수가 40회 이상인 고객은 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT customer_id FROM rental GROUP BY customer_id HAVING COUNT(*) >= 40) sub;", 46],
    ["총 결제 금액이 100달러 이상인 고객은 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT customer_id FROM payment GROUP BY customer_id HAVING SUM(amount) >= 100) sub;", 503],
    ["총 결제 금액이 200달러 이상인 고객은 몇 명인가요?", "SELECT COUNT(*) FROM (SELECT customer_id FROM payment GROUP BY customer_id HAVING SUM(amount) >= 200) sub;", 10],

    # 추가 복잡한 질문
    ["'Action' 카테고리에서 가장 긴 영화의 길이는?", "SELECT MAX(f.length) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Action';", 185],
    ["'Comedy' 카테고리에서 가장 짧은 영화의 길이는?", "SELECT MIN(f.length) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Comedy';", 46],
    ["'Drama' 카테고리 영화의 평균 대여료는?", "SELECT ROUND(AVG(f.rental_rate), 2) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Drama';", 3.02],
    ["'Sci-Fi' 카테고리 영화의 평균 길이는?", "SELECT ROUND(AVG(f.length), 2) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Sci-Fi';", 108.20],
    ["재고가 있는 영화는 몇 편인가요?", "SELECT COUNT(DISTINCT film_id) FROM inventory;", 958],
    ["재고가 없는 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE film_id NOT IN (SELECT DISTINCT film_id FROM inventory);", 42],
    ["대여 중인 영화는 몇 편인가요?", "SELECT COUNT(DISTINCT i.film_id) FROM inventory i JOIN rental r ON i.inventory_id = r.inventory_id WHERE r.return_date IS NULL;", 0],
    ["반납된 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE return_date IS NOT NULL;", 15861],
    ["반납되지 않은 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE return_date IS NULL;", 183],
    ["활성 고객은 몇 명인가요?", "SELECT COUNT(*) FROM customer WHERE active = 1;", 584],

    # 날짜/시간 관련
    ["2005년에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(YEAR FROM rental_date) = 2005;", 15844],
    ["2006년에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(YEAR FROM rental_date) = 2006;", 200],
    ["2월에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(MONTH FROM rental_date) = 2;", 2474],
    ["5월에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(MONTH FROM rental_date) = 5;", 1156],
    ["7월에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(MONTH FROM rental_date) = 7;", 6709],
    ["8월에 발생한 대여 건수는?", "SELECT COUNT(*) FROM rental WHERE EXTRACT(MONTH FROM rental_date) = 8;", 5705],

    # 집계 함수 추가
    ["전체 매출은 얼마인가요?", "SELECT ROUND(SUM(amount), 2) FROM payment;", 61312.04],
    ["평균 영화 길이는?", "SELECT ROUND(AVG(length), 2) FROM film;", 115.27],
    ["가장 긴 영화의 길이는?", "SELECT MAX(length) FROM film;", 185],
    ["가장 짧은 영화의 길이는?", "SELECT MIN(length) FROM film;", 46],
    
    # 추가 20개 (데이터베이스 실제 값 기반)
    ["'NC-17' 등급 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rating = 'NC-17';", 210],
    ["'G' 등급 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rating = 'G';", 178],
    ["대여료가 0.99인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_rate = 0.99;", 341],
    ["영화 길이가 50분 미만인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE length < 50;", 5],
    ["영화 길이가 180분 이상인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE length >= 180;", 39],
    ["대여 기간이 5일인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_duration = 5;", 191],
    ["대여 기간이 4일인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_duration = 4;", 203],
    ["대여 기간이 6일인 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film WHERE rental_duration = 6;", 212],
    ["'Family' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Family';", 69],
    ["'Animation' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Animation';", 66],
    ["'Documentary' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Documentary';", 68],
    ["'Sci-Fi' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Sci-Fi';", 61],
    ["'Travel' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Travel';", 57],
    ["'Children' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Children';", 60],
    ["'New' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'New';", 63],
    ["'Foreign' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Foreign';", 73],
    ["'Classics' 카테고리 영화는 몇 편인가요?", "SELECT COUNT(*) FROM film f JOIN film_category fc ON f.film_id = fc.film_id JOIN category c ON c.category_id = fc.category_id WHERE c.name = 'Classics';", 57],
    ["비활성 고객은 몇 명인가요?", "SELECT COUNT(*) FROM customer WHERE active = 0;", 15],
    ["Store 1의 고객은 몇 명인가요?", "SELECT COUNT(*) FROM customer WHERE store_id = 1;", 326],
    ["Store 2의 고객은 몇 명인가요?", "SELECT COUNT(*) FROM customer WHERE store_id = 2;", 273]
]

if __name__=="__main__":
    df = pd.DataFrame(data, columns=["question", "sql", "label"])
    csv_path = "experiments/dvdrental_testset.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"✅ 테스트셋 생성 완료: {csv_path}")
    print(f"📊 총 {len(df)}개의 테스트 케이스")
    print(f"\n💡 평가 방법:")
    print(f"   docker exec text2sql-web python /app/evaluate_testset.py")