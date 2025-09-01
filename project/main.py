from fastapi import FastAPI
from routers import ocr_router, vector_db_router, chat_router, normal_chat_router

# FastAPI 앱 생성
app = FastAPI(title="RAG System API")

# 라우터 등록
app.include_router(ocr_router.router, prefix="/rag", tags=["OCR"])

app.include_router(vector_db_router.router, prefix="/rag", tags=["VectorDB"])

app.include_router(chat_router.router, prefix="/rag", tags=["Chat"])

app.include_router(normal_chat_router.router, prefix="/normal", tags=["Chat"])

@app.get("/")
def root():
    return {"message": "RAG API is running!"}