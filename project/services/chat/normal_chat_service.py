import asyncio
from services.ocr.gemini_service import call_gemini

async def normal_chat_with_llm(user_id: str, query: str) -> str:
    prompt = f"""
        너는 나의 스터디 파트너야. 우리 같이 시험공부를 하고 있잖아.
        내가 공부에 대해 궁금한 걸 물어보면, 네가 아는 선에서 최대한 친절하게 설명해주는 역할이야.

        [너가 지켜야 할 규칙]
        1. 말투는 친구랑 같이 공부하는 것처럼, 편안하지만 내용은 정확하게 알려줘.
        2. 네가 모르는 내용이나 불확실한 정보에 대해서는 단정적으로 말하지 말고, '이 부분은 추측이야' 또는 '이건 확실하지 않은데'라고 솔직하게 말해줘.
        3. 답변은 핵심만 간단히 설명해줘.

        [사용자 질문]
        {query}
    """
    
    try:
        response = await asyncio.to_thread(call_gemini, prompt)
        return response.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "미안해. 답변을 만드는 데 문제가 생겼어."