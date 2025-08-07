from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_KEY or not GEMINI_KEY:
    print("[WARN] 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
