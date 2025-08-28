FROM python:3.12-slim

WORKDIR /app

# 시스템 도구 설치
# Git 설치 (GitHub 패키지 설치에 필요)
RUN apt-get update && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

# 시간대 환경 변수 설정 (한국 시간대)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Poppler 유틸리티 설치 (pdf2image 라이브러리에 필요)
# 이 부분이 pdfinfo 명령어를 제공합니다.
RUN apt-get update && apt-get install -y poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]