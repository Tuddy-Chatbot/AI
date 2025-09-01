from fastapi import APIRouter
from pydantic import BaseModel
from services.chat.normal_chat_service import normal_chat_with_llm
import time

router = APIRouter()

class NormalChatRequest(BaseModel):
    user_id: str
    query: str

@router.post("/chat")
async def normal_chat_endpoint(request: NormalChatRequest):
    """
    VectorDB를 사용하지않고 일반적인 챗봇 응답을 생성합니다.
    """
    # 시간
    timing = {}
    start_total = time.perf_counter()
    try:
        llm_response = await normal_chat_with_llm(
            user_id=request.user_id,
            query=request.query
        )
    finally:
        end = time.perf_counter()
        timing['normal_chat_response'] = round(end - start_total, 3)
        
    return{
        "status": "success",
        "user_id": request.user_id,
        "query": request.query,
        "response": llm_response,
        "timing": timing
    }