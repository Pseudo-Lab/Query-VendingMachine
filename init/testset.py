# 단일 정답에 대한 SQL 질의응답 테스트셋 생성 코드
import pandas as pd

data = [
    # 초급
    ["배우는 총 몇 명인가요?", "SELECT COUNT(*) FROM actor;", 200],
    ["고객은 총 몇 명인가요?", "SELECT COUNT(*) FROM customer;", 599],
    ["도시는 몇 개 있나요?", "SELECT COUNT(*) FROM city;", 600],
    ["국가는 몇 개 있나요?", "SELECT COUNT(*) FROM country;", 109],
    ["영화는 총 몇 편인가요?", "SELECT COUNT(*) FROM film;", 1000],
    ["언어는 몇 개 등록되어 있나요?", "SELECT COUNT(*) FROM language;", 6],
    ["성이 'Bergman'이고 이름이 'Liza'인 사람의 아이디는?", "SELECT actor_id FROM actor WHERE last_name = 'Bergman' AND first_name = 'Liza';", 121],
    ["‘PG’ 등급 영화의 평균 대여기간은 며칠인가요?", "SELECT AVG(rental_duration) FROM film WHERE rating = 'PG';", 5.00],
    ["이름에 ‘oo’가 들어간 배우는 총 몇 명인가요?", "SELECT COUNT(*) FROM actor WHERE first_name LIKE '%oo%';", 9],
    ["‘ACADEMY DINOSAUR’ 영화의 대여료는 얼마인가요?", "SELECT rental_rate FROM film WHERE title = 'ACADEMY DINOSAUR';", 0.99],

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
    ["평균 길이가 가장 짧은 카테고리는?", "SELECT c.name FROM category c JOIN film_category fc ON c.category_id = fc.category_id JOIN film f ON f.film_id = fc.film_id GROUP BY c.name ORDER BY AVG(f.length) ASC LIMIT 1;", "Sci-Fi"]
]

if __name__=="__main__":
    df = pd.DataFrame(data, columns=["question", "sql", "label"])
    csv_path = "./dvdrental_text2sql_test.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")