from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from services.chat.normal_chat_service import normal_chat_with_llm
import time

router = APIRouter()

class NormalChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    query: str
    n_turns: int = 6 # 입력값 생략 시, 기본값 6

@router.post("/chat")
async def normal_chat_endpoint(request: NormalChatRequest):
    """
    VectorDB 미사용 일반 챗 + 최근 히스토리 주입
    """
    # 시간
    timing = {}
    start_total = time.perf_counter()
    try:
        # session_id 없을때 테스트 용
        session_id = request.session_id or "local_test"
        
        llm_response = await normal_chat_with_llm(
            user_id=request.user_id,
            session_id=session_id,
            query=request.query,
            n_turns=request.n_turns
        )
    finally:
        end = time.perf_counter()
        timing['normal_chat_response'] = round(end - start_total, 3)
        
    return{
        "status": "success",
        "user_id": request.user_id,
        "session_id": request.session_id,
        "query": request.query,
        "response": llm_response,
        "timing": timing
    }