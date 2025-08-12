import os
from datetime import datetime

def create_session_dir(root: str = "output", user_id: str = None) -> str:
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    if user_id:
        session_dir = os.path.join(root, user_id, timestamp)
    else:
        session_dir = os.path.join(root, timestamp)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir