from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from services.chat.chat_service import chat_with_llm
from services.embedding.vector_db_service import search_documents
import time

router = APIRouter()

# Pydantic 모델을 사용하여 요청 본문 정의
class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None   # ← optional
    query: str
    n_turns: int = 6

INDEX_NAME = "rag-slides-index"

@router.post("/chat")
async def rag_chat_endpoint(request: ChatRequest):
    """
    RAG + 최근 히스토리 기반 챗
    """
    # 시간 로그
    timing = {}
    start_total = time.perf_counter()
    
    # 1. 벡터 데이터베이스에서 관련 문서 검색 (함수 직접 호출)
    start = time.perf_counter()
    try:
        results = search_documents(
            index_name=INDEX_NAME,
            namespace=request.user_id,
            query=request.query,
            k=3 # 검색할 문서의 수
        )
    except Exception as e:
        # 검색 실패 시, LLM에 컨텍스트 없이 질문
        print(f"Vector DB search failed: {e}")
        results = []
    finally:
        end = time.perf_counter()
        timing['vector_db_search'] = round(end - start, 3)

    # 2. 검색 결과를 바탕으로 LLM에 전달할 컨텍스트 생성
    source_documents = []
    context_chunks = []
    for doc, score in results:
        source_documents.append({
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score)
        })
        context_chunks.append(doc.page_content)

    context_text = "\n\n".join(context_chunks)

    # 3. LLM 서비스 호출하여 RAG 응답 생성
    start = time.perf_counter()
    try:
        # session_id 없을때 테스트 용
        session_id = request.session_id or "local_test"
        
        llm_response = await chat_with_llm(
            user_id=request.user_id,
            session_id=session_id,
            query=request.query,
            context=context_text,
            n_turns=request.n_turns
        )
    finally:
        end = time.perf_counter()
        timing['llm_response'] = round(end - start, 3)
        
    timing['total_endpoint'] = round(time.perf_counter() - start_total, 3)
    
    return {
        "status": "success",
        "user_id": request.user_id,
        "session_id": request.session_id,
        "query": request.query,
        "response": llm_response,
        "source_documents": source_documents,
        "timing": timing
    }

