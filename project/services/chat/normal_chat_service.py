import asyncio
from services.ocr.gemini_service import call_gemini
from services.chat.history_service import load_recent_turns, append_turn
from typing import List, Tuple

def _format_history(pairs: List[Tuple[str, str]]) -> str:
    if not pairs:
        return "없음"
    lines = []
    for i, (u, a) in enumerate(pairs, start=1):
        lines.append(f"[대화 {i}]")
        lines.append(f"User: {u}")
        lines.append(f"Assistant: {a}")
    return "\n".join(lines)

async def normal_chat_with_llm(
    user_id: str,
    session_id: str,
    query: str,
    n_turns: int
) -> str:
    
    # n_turns 가드 (0이면 히스토리 주입 끔, 상한 50)
    effective_n = max(0, min(n_turns, 50))
    if effective_n == 0:
        recent_pairs = []
    else:
        recent_pairs = load_recent_turns(user_id, session_id, effective_n)

    history_block = _format_history(recent_pairs)
    
    prompt = f"""
너는 나의 스터디 파트너야. 일반 지식으로도 너가 아는 선에서 최대한 정확하게 답해줘.

[대화 히스토리 (최근 {effective_n}턴)]
{history_block}

[지시사항]
1. 말투는 스터디 파트너랑 같이 공부하는 느낌 (편안하지만 정확하게)
2. 단정 짓지 말고, 불확실하면 '추측입니다' 또는 '확실하지 않음'이라고 알려주기
3. 답변은 핵심 위주로 간단히

[사용자 질문]
{query}
""".strip()
    
    try:
        response = await asyncio.to_thread(call_gemini, prompt)
        answer = response.strip()
        append_turn(user_id, session_id, query, answer)
        return answer
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "미안해. 답변을 만드는 데 문제가 생겼어."