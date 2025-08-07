import os
from datetime import datetime

def create_session_dir(root: str = "output") -> str:
    timestamp = datetime.now().strftime("%y%m%d-%H%M")
    session_dir = os.path.join(root, timestamp)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir
