# 실무 중심의 Unique한 SQL 질의응답 테스트셋 (100개)
import pandas as pd

data = [
    # 1단계 - 단일 테이블에 대한 집계 및 단순 조건 조회 (예를 들어 SELECT, FROM, WHERE 하나씩 사용.)
    # 모든 테이블당 2개의 질의응답 쌍 생성
    ["이름이 Penelope인 배우는 총 몇 명인가?", "SELECT COUNT(*) FROM actor WHERE first_name = 'Penelope';", 4],
    ["배우 데이터베이스에서 이름이 페넬로페인 사람의 수를 세어줘.", "SELECT COUNT(*) FROM actor WHERE first_name = 'Penelope';", 4],

    ["California인 주소의 개수를 구해줘.", "SELECT COUNT(*) FROM address WHERE district = 'California';", 9],
    ["캘리포니아 지역으로 등록된 주소가 몇 건인지 알려줘.", "SELECT COUNT(*) FROM address WHERE district = 'California';", 9],

    ["카테고리 ID가 1번인 카테고리의 이름은 무엇인가?", "SELECT name FROM category WHERE category_id = 1;", 'Action'],
    ["식별 번호가 1인 영화 장르를 알려줘.", "SELECT name FROM category WHERE category_id = 1;", 'Action'],

    ["국가 ID가 44번인 도시의 총 개수는?", "SELECT COUNT(*) FROM city WHERE country_id = 44;", 60],
    ["44번 국가 코드에 소속된 도시가 몇 군데인지 카운트해.", "SELECT COUNT(*) FROM city WHERE country_id = 44;", 60],

    ["비활성 고객의 수를 세어줘.", "SELECT COUNT(*) FROM customer WHERE active = 0;", 15],
    ["현재 활동 중이지 않은 손님은 총 몇 명이야?", "SELECT COUNT(*) FROM customer WHERE active = 0;", 15],

    ["영화 테이블에서 상영 시간의 최댓값을 구해줘.", "SELECT MAX(length) FROM film;", 185],
    ["등록된 영화 중 가장 긴 러닝타임은 몇 분이야?", "SELECT MAX(length) FROM film;", 185],

    ["배우 ID가 1번인 배우가 출연한 영화의 총 편수는?", "SELECT COUNT(*) FROM film_actor WHERE actor_id = 1;", 19],
    ["1번 배우와 연결된 영화 레코드는 몇 개가 있어?", "SELECT COUNT(*) FROM film_actor WHERE actor_id = 1;", 19],

    ["카테고리 ID가 6번인 영화의 총 개수를 조회해.", "SELECT COUNT(*) FROM film_category WHERE category_id = 6;", 68],
    ["6번 장르로 분류된 영화가 몇 편인지 숫자로 알려줘.", "SELECT COUNT(*) FROM film_category WHERE category_id = 6;", 68],

    ["영화 ID가 1번인 영화의 전체 재고 수량은 몇 개인가?", "SELECT COUNT(*) FROM inventory WHERE film_id = 1;", 8],
    ["매장에 있는 1번 영화의 총 개수를 세어줘.", "SELECT COUNT(*) FROM inventory WHERE film_id = 1;", 8],

    ["언어 ID가 1번인 언어의 이름은?", "SELECT name FROM language WHERE language_id = 1;", 'English'],
    ["1번 랭귀지 코드에 해당하는 언어 명칭을 출력해.", "SELECT name FROM language WHERE language_id = 1;", 'English'],

    ["결제 테이블에서 가장 큰 금액은 얼마인가?", "SELECT MAX(amount) FROM payment;", 11.99],
    ["지금까지 발생한 결제 내역 중 최고 액수를 알려줘.", "SELECT MAX(amount) FROM payment;", 11.99],

    ["직원 ID가 1번인 직원이 처리한 대여 건수는 총 몇 개인가?", "SELECT COUNT(*) FROM rental WHERE staff_id = 1;", 8040],
    ["1번 스태프가 담당했던 렌탈 기록의 총합을 구해줘.", "SELECT COUNT(*) FROM rental WHERE staff_id = 1;", 8040],

    ["직원 ID가 2번인 직원의 이메일 주소는 무엇인가?", "SELECT email FROM staff WHERE staff_id = 2;", 'Jon.Stephens@sakilastaff.com'],
    ["2번 사원의 이메일 정보를 하나만 딱 보여줘.", "SELECT email FROM staff WHERE staff_id = 2;", 'Jon.Stephens@sakilastaff.com'],

    ["매장 ID가 1번인 매장의 매니저 직원 ID는 몇 번인가?", "SELECT manager_staff_id FROM store WHERE store_id = 1;", 1],
    ["1호점을 관리하는 매니저의 사원 번호를 알려줘.", "SELECT manager_staff_id FROM store WHERE store_id = 1;", 1],

    ["국가 테이블에 등록된 전체 국가 수는?", "SELECT COUNT(*) FROM country;", 109],
    ["등록된 나라가 총 몇 개인지 알려줘.", "SELECT COUNT(*) FROM country;", 109],

    ["대여료가 0.99달러인 영화는 몇 편인가?", "SELECT COUNT(*) FROM film WHERE rental_rate = 0.99;", 341],
    ["렌탈 비용이 0.99달러로 설정된 영화의 총 개수를 구해줘.", "SELECT COUNT(*) FROM film WHERE rental_rate = 0.99;", 341],

    # 2단계 - 다중 테이블 조인 및 복합 조건 조회 (예를 들어 JOIN, GROUP BY, HAVING, ORDER BY 등 추가 사용.)
    # 조인 (film + language)
    ["'Academy Dinosaur' 영화의 언어 이름은 무엇인가?", "SELECT L.name FROM film AS F JOIN language AS L ON F.language_id = L.language_id WHERE F.title = 'Academy Dinosaur';", 'English'],
    ["제목이 'ACADEMY DINOSAUR'인 영화의 언어 명칭을 알려줘.", "SELECT L.name FROM film AS F JOIN language AS L ON F.language_id = L.language_id WHERE F.title = 'Academy Dinosaur';", 'English'],

    # 조인 + 집계 (film_actor + actor)
    ["배우 'Penelope Guiness'가 출연한 영화의 총 개수를 구해줘.", "SELECT COUNT(FA.film_id) FROM film_actor AS FA JOIN actor AS A ON FA.actor_id = A.actor_id WHERE A.first_name = 'Penelope' AND A.last_name = 'Guiness';", 19],
    ["성(last_name)이 Guiness이고 이름이 Penelope인 배우가 출연한 영화는 총 몇 편인가?", "SELECT COUNT(FA.film_id) FROM film_actor AS FA JOIN actor AS A ON FA.actor_id = A.actor_id WHERE A.first_name = 'Penelope' AND A.last_name = 'Guiness';", 19],

    # 그룹화 및 순서 (customer + payment)
    ["가장 많은 금액을 지출한 고객의 고객 ID는 무엇인가?", "SELECT customer_id FROM payment GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 1;", 148],
    ["총 결제 금액이 가장 높은 고객의 식별 번호를 알려줘.", "SELECT customer_id FROM payment GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 1;", 148],

    # 조인 및 복합 조건 (customer + address + country + city)
    ["Canada에 거주하는 고객의 총 수는 몇 명인가?", "SELECT COUNT(C.customer_id) FROM customer AS C JOIN address AS A ON C.address_id = A.address_id JOIN city AS CI ON A.city_id = CI.city_id JOIN country AS CO ON CI.country_id = CO.country_id WHERE CO.country = 'Canada';", 5],
    ["'Canada' 국가에 주소를 둔 손님은 모두 몇 명인지 세어줘.", "SELECT COUNT(T1.customer_id) FROM customer AS T1 INNER JOIN address AS T2 ON T1.address_id = T2.address_id INNER JOIN city AS T3 ON T2.city_id = T3.city_id INNER JOIN country AS T4 ON T3.country_id = T4.country_id WHERE T4.country = 'Canada';", 5],

    # 조인 및 필터링 (inventory + store)
    ["직원 Mike Hillyer가 관리하는 매장의 총 재고 수량은 몇 개인가?", "SELECT COUNT(I.inventory_id) FROM inventory AS I JOIN store AS S ON I.store_id = S.store_id JOIN staff AS ST ON S.manager_staff_id = ST.staff_id WHERE ST.first_name = 'Mike' AND ST.last_name = 'Hillyer';", 2270],
    ["매니저 이름이 'Mike Hillyer'인 매점의 재고 레코드는 총 몇 건인가?", "SELECT COUNT(T1.inventory_id) FROM inventory AS T1 INNER JOIN store AS T2 ON T1.store_id = T2.store_id INNER JOIN staff AS T3 ON T2.manager_staff_id = T3.staff_id WHERE T3.first_name = 'Mike' AND T3.last_name = 'Hillyer';", 2270],

    # 그룹화 및 조건 (rental)
    ["대여 건수가 가장 많은 직원의 ID는 무엇인가?", "SELECT staff_id FROM rental GROUP BY staff_id ORDER BY COUNT(rental_id) DESC LIMIT 1;", 1],
    ["총 렌탈 건수가 가장 높은 직원 한 명의 식별 번호를 알려줘.", "SELECT staff_id FROM rental GROUP BY staff_id ORDER BY COUNT(rental_id) DESC LIMIT 1;", 1],

    # 조인 및 정렬 (film + film_category + category)
    ["'Action' 장르에 속하는 영화 중 상영 시간이 가장 긴 영화의 제목은?", "SELECT T1.title FROM film AS T1 INNER JOIN film_category AS T2 ON T1.film_id = T2.film_id INNER JOIN category AS T3 ON T2.category_id = T3.category_id WHERE T3.name = 'Action' ORDER BY T1.length DESC LIMIT 1;", 'Darn Forrester'],
    ["액션 카테고리에 있는 영화 중 러닝타임이 제일 긴 영화 제목을 하나만 출력해.", "SELECT T1.title FROM film AS T1 INNER JOIN film_category AS T2 ON T1.film_id = T2.film_id INNER JOIN category AS T3 ON T2.category_id = T3.category_id WHERE T3.name = 'Action' ORDER BY T1.length DESC LIMIT 1;", 'Darn Forrester'],

    # 조인 및 집계 (rental + payment)
    ["2005년 5월에 발생한 총 결제 금액은 얼마인가?", "SELECT ROUND(SUM(P.amount), 2) FROM payment AS P WHERE EXTRACT(YEAR FROM P.payment_date) = 2005 AND EXTRACT(MONTH FROM P.payment_date) = 5;", 4824.43],
    ["2005년 5월 한 달간의 결제 총액을 소수점 둘째 자리까지 알려줘.", "SELECT ROUND(SUM(P.amount), 2) FROM payment AS P WHERE EXTRACT(YEAR FROM P.payment_date) = 2005 AND EXTRACT(MONTH FROM P.payment_date) = 5;", 4824.43],

    # 조인 및 그룹화 (film + inventory + rental)
    ["가장 많이 대여된 영화 ID는 무엇인가?", "SELECT I.film_id FROM inventory AS I JOIN rental AS R ON I.inventory_id = R.inventory_id GROUP BY I.film_id ORDER BY COUNT(R.rental_id) DESC LIMIT 1;", 103],
    ["렌탈 횟수가 가장 높은 영화의 식별 번호를 알려줘.", "SELECT I.film_id FROM inventory AS I JOIN rental AS R ON I.inventory_id = R.inventory_id GROUP BY I.film_id ORDER BY COUNT(R.rental_id) DESC LIMIT 1;", 103],

    # 복합 조인 (city + address + customer)
    ["'London' 도시에 거주하는 고객은 몇 명인가?", "SELECT COUNT(C.customer_id) FROM customer AS C JOIN address AS A ON C.address_id = A.address_id JOIN city AS CI ON A.city_id = CI.city_id WHERE CI.city = 'London';", 2],
    ["런던에 주소를 둔 손님의 총 수를 세어줘.", "SELECT COUNT(C.customer_id) FROM customer AS C JOIN address AS A ON C.address_id = A.address_id JOIN city AS CI ON A.city_id = CI.city_id WHERE CI.city = 'London';", 2],

    # 조인 및 평균 (payment + customer)
    ["고객별 평균 결제 금액 중 가장 높은 금액은 얼마인가?", "SELECT ROUND(AVG(P.amount), 2) FROM payment AS P GROUP BY P.customer_id ORDER BY AVG(P.amount) DESC LIMIT 1;", 5.65],
    ["손님 한 명당 평균 결제액이 가장 큰 고객의 평균 금액을 알려줘.", "SELECT ROUND(AVG(P.amount), 2) FROM payment AS P GROUP BY P.customer_id ORDER BY AVG(P.amount) DESC LIMIT 1;", 5.65],

    # 조인 및 필터링 (film + film_category + category)
    ["'Comedy' 장르 영화의 평균 대여료는 얼마인가?", "SELECT ROUND(AVG(F.rental_rate), 2) FROM film AS F JOIN film_category AS FC ON F.film_id = FC.film_id JOIN category AS C ON FC.category_id = C.category_id WHERE C.name = 'Comedy';", 3.16],
    ["코미디 카테고리에 속한 영화들의 평균 렌탈 비용을 알려줘.", "SELECT ROUND(AVG(F.rental_rate), 2) FROM film AS F JOIN film_category AS FC ON F.film_id = FC.film_id JOIN category AS C ON FC.category_id = C.category_id WHERE C.name = 'Comedy';", 3.16],

    # 조인 및 집계 (actor + film_actor + film)
    ["배우 ID가 5번인 배우가 출연한 영화들의 평균 길이는?", "SELECT ROUND(AVG(F.length), 2) FROM film AS F JOIN film_actor AS FA ON F.film_id = FA.film_id WHERE FA.actor_id = 5;", 111.77],
    ["5번 배우가 출연한 영화들의 평균 상영 시간을 구해줘.", "SELECT ROUND(AVG(F.length), 2) FROM film AS F JOIN film_actor AS FA ON F.film_id = FA.film_id WHERE FA.actor_id = 5;", 111.77],

    # 조인 및 그룹화 (rental + customer)
    ["대여 횟수가 30회 이상인 고객은 몇 명인가?", "SELECT COUNT(DISTINCT R.customer_id) FROM rental AS R GROUP BY R.customer_id HAVING COUNT(R.rental_id) >= 30;", 236],
    ["렌탈을 30번 이상 한 손님의 총 수를 알려줘.", "SELECT COUNT(DISTINCT R.customer_id) FROM rental AS R GROUP BY R.customer_id HAVING COUNT(R.rental_id) >= 30;", 236],

]

if __name__=="__main__":
    df = pd.DataFrame(data, columns=["question", "sql", "label"])
    csv_path = "experiments/dvdrental_testset.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"✅ 테스트셋 생성 완료: {csv_path}")
    print(f"📊 총 {len(df)}개의 테스트 케이스")
    print(f"\n💡 평가 방법:")
    print(f"   docker exec text2sql-web python /app/evaluate_testset.py")
