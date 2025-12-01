#!/bin/bash
# Docker 컨테이너 내부에서 평가 실행

echo "🐳 Docker 컨테이너 내부에서 평가 실행..."

# text2sql-web 컨테이너에서 평가 스크립트 실행
docker exec -it text2sql-web python /app/evaluate_testset.py

echo "✅ 완료!"
