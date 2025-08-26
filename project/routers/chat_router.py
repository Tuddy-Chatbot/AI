from fastapi import APIRouter
from pydantic import BaseModel
from services.chat.chat_service import chat_with_llm
from services.embedding.vector_db_service import search_documents
from services.embedding.embedding_service import get_embedding_model
import time

router = APIRouter()

# Pydantic 모델을 사용하여 요청 본문 정의
class ChatRequest(BaseModel):
    user_id: str
    query: str

# 공용 임베딩 모델 초기화
embedding_model = get_embedding_model()
INDEX_NAME = "rag-slides-index"

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    사용자의 질문을 기반으로 RAG(Retrieval-Augmented Generation) 챗봇 응답을 생성합니다.
    """
    # 시간 로그
    timing = {}
    start_total = time.perf_counter()
    
    # 1. 벡터 데이터베이스에서 관련 문서 검색 (함수 직접 호출)
    start = time.perf_counter()
    try:
        search_results_raw = search_documents(
            embedding_model=embedding_model,
            index_name=INDEX_NAME,
            namespace=request.user_id,
            query=request.query,
            k=3 # 검색할 문서의 수
        )
    except Exception as e:
        # 검색 실패 시, LLM에 컨텍스트 없이 질문
        print(f"Vector DB search failed: {e}")
        search_results_raw = []
    finally:
        end = time.perf_counter()
        timing['vector_db_search'] = round(end - start, 3)

    # 2. 검색 결과를 바탕으로 LLM에 전달할 컨텍스트 생성
    context = ""
    source_documents = []
    if search_results_raw:
        # 검색된 문서들의 내용을 하나의 문자열로 결합하고 출력을 위한 리스트 포맷
        source_documents = [
            {
                "score": float(score),
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc, score in search_results_raw
        ]
        context = " ".join([doc['content'] for doc in source_documents])

    # 3. LLM 서비스 호출하여 RAG 응답 생성
    start = time.perf_counter()
    try:
        llm_response = await chat_with_llm(
            user_id=request.user_id,
            query=request.query,
            context=context
        )
    finally:
        end = time.perf_counter()
        timing['llm_response'] = round(end - start, 3)
        
    timing['total_endpoint'] = round(time.perf_counter() - start_total, 3)
    
    return {
        "status": "success",
        "user_id": request.user_id,
        "query": request.query,
        "response": llm_response,
        "source_documents": source_documents,
        "timing": timing
    }

