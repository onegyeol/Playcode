FROM python:3.12-slim

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc pkg-config libssl-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉터리 설정
WORKDIR /app

# requirements.txt 복사 후 필요한 패키지 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# wait-for-it.sh 복사 및 실행 가능하도록 설정
COPY wait-for-it.sh /usr/local/bin/wait-for-it
RUN chmod +x /usr/local/bin/wait-for-it

# 포트 설정
EXPOSE 8000

# 기본 실행 명령: 데이터베이스가 준비될 때까지 기다리며 마이그레이션 실행 후 서버 실행
CMD ["sh", "-c", "wait-for-it my-django-db:3306 -- python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
