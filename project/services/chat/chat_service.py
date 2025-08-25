import asyncio
from services.ocr.gemini_service import call_gemini

async def chat_with_llm(user_id: str, query: str, context: str) -> str:
    """
    RAG 컨텍스트를 사용하여 Gemini LLM과 채팅합니다.
    강의 자료를 우선으로 하되, 필요하면 일반 지식으로 보강합니다.
    """
    context_text = context if context else "없음"

    prompt = f"""
        너는 나의 스터디 파트너야. 우리는 시험을 준비하기 위해 강의 자료를 같이 보면서 공부하고 있어.
        너의 역할은:
        1. 제공된 강의 자료를 최우선으로 참고해서 대화하듯 답하기
        2. 강의 자료에 없으면 일반 지식으로 보강하되, 그 부분은 [일반 지식]이라고 표시하기
        3. 단정 짓지 말고, 불확실하면 '추측입니다' 또는 '확실하지 않음'이라고 알려주기
        4. 말투는 친구랑 같이 공부하는 느낌 (편안하지만 정확하게)

        [강의 자료 컨텍스트]
        {context_text}

        [사용자 질문]
        {query}
        """

    try:
        # 동기 함수인 call_gemini를 비동기적으로 실행
        response = await asyncio.to_thread(call_gemini, prompt)
        return response.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "미안해. 답변을 만드는 데 문제가 생겼어."