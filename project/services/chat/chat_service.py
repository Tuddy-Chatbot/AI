import asyncio
from typing import List, Tuple, Optional, Dict
from services.ocr.gemini_service import call_gemini
from services.chat.history_service import load_recent_turns, append_turn

def _format_history_for_prompt(pairs: List[Tuple[str, str]]) -> str:
    """
    최근 대화 N턴을 프롬프트에 안전하게 삽입하기 위한 간단한 포맷터
    """
    if not pairs:
        return "없음"
    lines = []
    for i, (u, a) in enumerate(pairs, start=1):
        lines.append(f"[대화 {i}]")
        lines.append(f"User: {u}")
        lines.append(f"Assistant: {a}")
    return "\n".join(lines)

def _build_text_prompt(history_block: str, context_text: str, query: str, effective_n: int) -> str:
    """텍스트 전용 요청을 위한 프롬프트"""
    return f"""
너는 나의 스터디 파트너야. 우리는 시험을 준비하기 위해 강의 자료를 같이 보면서 공부하고 있어.

[대화 히스토리 (최근 {effective_n}턴)]
{history_block}

[강의 자료 컨텍스트]
{context_text}

[지시사항]
1. 제공된 강의 자료를 최우선으로 참고해서 대화하듯 답하기(참고한 강의 자료의 출처 명시 ex) [슬라이드 6])
2. 강의 자료에 없으면 일반 지식으로 보강하되, 그 부분은 [일반 지식]이라고 표시하기
3. 단정 짓지 말고, 불확실하면 '추측입니다' 또는 '확실하지 않음'이라고 알려주기
4. 말투는 스터디 파트너랑 같이 공부하는 느낌 (편안하지만 정확하게)

[사용자 질문]
{query}
""".strip()

def _build_multimodal_prompt(history_block: str, context_text: str, query: str, effective_n: int) -> str:
    """이미지 + 텍스트 요청을 위한 프롬프트"""
    return f"""
너는 나의 스터디 파트너이자 이미지 분석가야. 우리는 강의 자료와 이미지를 함께 보며 공부하고 있어.

[대화 히스토리 (최근 {effective_n}턴)]
{history_block}

[강의 자료 컨텍스트]
{context_text}

[지시사항]
1. **제공된 이미지를 최우선으로, 가장 중요하게 분석**해서 답변을 생성해줘.
2. 이미지 분석 후, 필요하다면 강의 자료 컨텍스트를 참고하여 답변을 보충해줘.(만약 참고했다면 참고한 강의 자료의 출처 명시 ex) [슬라이드 6])
3. 말투는 스터디 파트너랑 같이 공부하는 느낌 (편안하지만 정확하게)

[사용자 질문]
{query}
""".strip()

async def chat_with_llm(
    user_id: str,
    session_id: str,
    query: str,
    context: str,
    n_turns: int,
    images: Optional[List[Dict]] = None
) -> str:
    """
    RAG 컨텍스트 + 최근 N턴 히스토리를 반영하여 Gemini 호출
    """
    
    # n_turns 가드 (0이면 히스토리 주입 끔, 상한 50)
    effective_n = max(0, min(n_turns, 50))
    if effective_n == 0:
        recent_pairs = []
    else:
        recent_pairs = load_recent_turns(user_id, session_id, effective_n)

    history_block = _format_history_for_prompt(recent_pairs)
    context_text = context or "없음"
    
    # 이미지 유무에 따라 적절한 프롬프트 빌더 함수 호출
    if images:
        prompt = _build_multimodal_prompt(history_block, context_text, query, effective_n)
    else:
        prompt = _build_text_prompt(history_block, context_text, query, effective_n)

    try:
        # 동기 함수인 call_gemini를 비동기적으로 실행
        response = await asyncio.to_thread(
            call_gemini, prompt, images=images
        )
        answer = response.strip()
        # 히스토리에 이번 턴 저장
        append_turn(user_id, session_id, query, answer)
        return answer
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "미안해. 답변을 만드는 데 문제가 생겼어."