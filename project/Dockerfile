# ====================================================================
# 스테이지 1: 'builder' - 라이브러리 설치 및 빌드를 위한 환경
# ====================================================================
FROM python:3.12 AS builder

# 작업 디렉토리 설정
WORKDIR /app

# 빌드에 필요한 시스템 도구 설치 (git)
RUN apt-get update && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사
COPY requirements.txt .

# --prefix=/install 옵션을 사용하여 모든 파이썬 라이브러리를 /install 폴더에 격리하여 설치
# 이 폴더를 나중에 최종 이미지로 복사할 예정
RUN pip install --prefix=/install -r requirements.txt


# ====================================================================
# 스테이지 2: 'final' - 실제 애플리케이션 실행을 위한 최종 이미지
# ====================================================================
FROM python:3.12-slim

# 시간대 환경 변수 설정 (한국 시간대)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# '실행'에 필요한 시스템 도구만 설치 (poppler-utils)
# git과 같은 빌드용 도구는 여기에 포함되지 않아 이미지가 가벼워짐
RUN apt-get update && apt-get install -y poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# [핵심] builder 스테이지의 /install 폴더에서 '설치된 라이브러리'만 복사
COPY --from=builder /install /usr/local

# 소스 코드 복사
COPY . .

# 컨테이너 실행 명령어
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]