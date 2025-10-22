FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 컨테이너 실행 시 Streamlit 앱 시작
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
