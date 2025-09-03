# syntax=docker/dockerfile:1

# ====================================================================
# 스테이지 1: 'builder' - 의존성 설치를 위한 빌드 환경
# ====================================================================
FROM python:3.12-slim AS builder

# ... (이하 내용은 이전과 동일) ...
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ====================================================================
# 스테이지 2: 'final' - 실제 애플리케이션 실행을 위한 최종 이미지
# ====================================================================
FROM python:3.12-slim

# ... (이하 내용은 이전과 동일) ...
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health',timeout=4).status==200 else 1)"