from typing import List, Tuple, Optional
import os
from functools import lru_cache
from redis import Redis as RedisClient
from langchain_redis.chat_message_history import RedisChatMessageHistory
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
import re

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("환경변수 REDIS_URL이 필요합니다.")

# prefix/ttl은 기본값 허용이 더 안전
KEY_PREFIX = os.getenv("CHAT_HISTORY_KEY_PREFIX", "tuddy:chat:")
_ttl_raw = os.getenv("REDIS_TTL_SECONDS", "").strip()
TTL: Optional[int]
if _ttl_raw == "":
    TTL = None  # 미설정이면 TTL 미적용
else:
    try:
        TTL = int(_ttl_raw)
        if TTL <= 0:
            TTL = None  # 0 이하도 미적용 처리
    except ValueError:
        TTL = None
        
SAFE_RE = re.compile(r'[^0-9A-Za-z_]')

def _sanitize(s: str) -> str:
    return SAFE_RE.sub('_', s)

def _session_key(user_id: str, session_id: str) -> str:
    # 접두사/아이디에서 특수문자 제거(콜론 포함)
    return f"{_sanitize(KEY_PREFIX)}{_sanitize(user_id)}_{_sanitize(session_id)}"

@lru_cache(maxsize=1)
def _get_redis_client() -> RedisClient:
    return RedisClient.from_url(
        REDIS_URL,
        socket_timeout=5,           # 개별 커맨드 최대 대기
        socket_connect_timeout=5,   # 연결 시도 타임아웃
        health_check_interval=30,   # 커넥션 keepalive/헬스체크
        retry_on_timeout=True,      # 타임아웃 시 재시도
        # decode_responses=False,   # 필요 시 텍스트 디코딩
        # max_connections=100,      # QPS 높으면 풀 상한 지정
    )

def get_history(user_id: str, session_id: str) -> RedisChatMessageHistory:
    client = _get_redis_client()
    return RedisChatMessageHistory(
        session_id=_session_key(user_id, session_id),
        redis_client=client,   # ← 버전 중립 & 일반 Redis 호환
        ttl=TTL
    )

def load_recent_turns(
    user_id: str, session_id: str, n_turns: int
) -> List[Tuple[str, str]]:
    hist = get_history(user_id, session_id)
    messages: List[BaseMessage] = hist.messages # 삽입순으로 정렬된걸 반환

    pairs: List[Tuple[str, str]] = []
    pending_human: Optional[str] = None
    for m in messages:
        if isinstance(m, HumanMessage):
            pending_human = m.content
        elif isinstance(m, AIMessage):
            if pending_human is not None:
                pairs.append((pending_human, m.content))
                pending_human = None

    if n_turns > 0 and len(pairs) > n_turns:
        # 슬라이싱으로 n_turns > 실제 pair 여도 문제 없음
        pairs = pairs[-n_turns:]
    return pairs

def append_turn(user_id: str, session_id: str, user_text: str, ai_text: str) -> None:
    hist = get_history(user_id, session_id)
    hist.add_user_message(user_text)
    hist.add_ai_message(ai_text)

def clear_session(user_id: str, session_id: str) -> None:
    hist = get_history(user_id, session_id)
    hist.clear()
