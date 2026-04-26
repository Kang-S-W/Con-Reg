import json
import os

FILE_PATH = "history.json"

def load_history():
    """파일에서 기록을 읽어오되, 파일이 없으면 빈 리스트를 반환합니다."""
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(history_list):
    """기록을 파일에 즉시 저장합니다."""
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)
