import asyncio
from services.ocr.gemini_service import call_gemini

async def chat_with_llm(user_id: str, query: str, context: str) -> str:
    """
    RAG 컨텍스트를 사용하여 Gemini LLM과 채팅합니다.
    """
    if not context:
        # 컨텍스트가 없는 경우 일반적인 질문에 대한 답변을 유도
        prompt = f"""
        안녕하세요! 강의 자료에서는 관련 내용을 찾지 못했습니다.
        사용자 질문: {query}
        """
    else:
        # 사용자 질문과 벡터 DB에서 검색된 컨텍스트를 결합하여 Gemini에게 보낼 프롬프트를 생성
        prompt = f"""
        ---
        제공된 강의 자료 컨텍스트:
        {context}
        ---
        
        위의 강의 자료 컨텍스트를 기반으로 다음 사용자 질문에 답변하세요.
        만약 컨텍스트에 답변이 없는 경우, "강의 자료에서 관련 내용을 찾지 못했습니다."라고 답변하세요.

        사용자 질문: {query}
        """
    
    # 동기 함수인 call_gemini를 비동기적으로 실행
    try:
        response = await asyncio.to_thread(call_gemini, prompt)
        return response.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "죄송합니다. 답변을 생성하는 데 문제가 발생했습니다."
