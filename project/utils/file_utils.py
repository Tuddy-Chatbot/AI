import os
from datetime import datetime

def create_session_dir(root: str = "output", user_id: str = None) -> str:
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    if user_id:
        session_dir = os.path.join(root, user_id, timestamp)
    else:
        session_dir = os.path.join(root, timestamp)
    # exist_ok는 같은 디렉토리가 이미 존재할 때, 에러 없이 작업을 마친다는 코드
    os.makedirs(session_dir, exist_ok=True)
    return session_dir