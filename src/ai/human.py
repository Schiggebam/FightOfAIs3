from typing import Dict, Any, Tuple

from src.ai.AI_GameStatus import AI_Move




def set_flag():
    global boom
    boom = True

def check_input() -> Tuple[AI_Move, Dict[str, Any], bool]:
    return None, None, boom
