from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from services.chat.normal_chat_service import normal_chat_with_llm
import time

router = APIRouter()

@router.post("/chat")
async def normal_chat_endpoint(
    user_id: str = Form(...),
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    n_turns: int = Form(6),
    files: List[UploadFile] = File(default_factory=list) # 여러 이미지 파일(선택 사항)
):
    """
    VectorDB 미사용 일반 챗 + 최근 히스토리 기반 챗 (이미지 첨부 가능)
    """
    
    # 첨부 이미지 개수 제한
    if len(files) > 3:
        raise HTTPException(
            status_code=400,  # 400 Bad Request 에러
            detail="이미지는 최대 3개까지만 업로드할 수 있습니다."
        )
    
    timing = {}
    start_total = time.perf_counter()
    
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
    
    start = time.perf_counter()
    try:
        # session_id 없을때 테스트 용
        effective_session_id = session_id or "local_test"
        
        llm_response = await normal_chat_with_llm(
            user_id=user_id,
            session_id=effective_session_id,
            query=query,
            n_turns=n_turns,
            images=list_of_images
        )
    finally:
        end = time.perf_counter()
        timing['llm_response'] = round(end - start, 3)
        
    timing['total_endpoint'] = round(time.perf_counter() - start_total, 3)
        
    return{
        "status": "success",
        "user_id": user_id,
        "session_id": session_id,
        "query": query,
        "response": llm_response,
        "timing": timing
    }