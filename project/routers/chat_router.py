from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from services.chat.chat_service import chat_with_llm
from services.embedding.vector_db_service import search_documents
import time

router = APIRouter()

INDEX_NAME = "rag-slides-index"

@router.post("/chat")
async def rag_chat_endpoint(
    user_id: str = Form(...),
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    n_turns: int = Form(6),
    files: List[UploadFile] = File(default_factory=list) # 여러 이미지 파일(선택 사항)
):
    """
    RAG + 최근 히스토리 기반 챗 (이미지 첨부 가능)
    """
    
    # 첨부 이미지 개수 제한
    if len(files) > 3:
        raise HTTPException(
            status_code=400,  # 400 Bad Request 에러
            detail="이미지는 최대 3개까지만 업로드할 수 있습니다."
        )
    
    timing = {}
    start_total = time.perf_counter()
    
    # 1. 벡터 데이터베이스에서 관련 문서 검색 (함수 직접 호출)
    start = time.perf_counter()
    try:
        results = search_documents(
            index_name=INDEX_NAME,
            namespace=user_id,
            query=query,
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
    
    # 이미지 데이터 처리
    list_of_images = []
    start = time.perf_counter()
    if files:
        for file in files:
            image_data = {
                "mime_type": file.content_type,
                "data": await file.read()
            }
            list_of_images.append(image_data)
    end = time.perf_counter()
    timing['image_processing'] = round(end - start, 3)

    # 3. LLM 서비스 호출하여 RAG 응답 생성
    start = time.perf_counter()
    try:
        # session_id 없을때 테스트 용
        effective_session_id = session_id or "local_test"
        
        llm_response = await chat_with_llm(
            user_id=user_id,
            session_id=effective_session_id,
            query=query,
            context=context_text,
            n_turns=n_turns,
            images=list_of_images
        )
    finally:
        end = time.perf_counter()
        timing['llm_response'] = round(end - start, 3)
        
    timing['total_endpoint'] = round(time.perf_counter() - start_total, 3)
    
    return {
        "status": "success",
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "response": llm_response,
        "source_documents": source_documents,
        "timing": timing
    }

