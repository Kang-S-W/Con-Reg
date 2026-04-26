import json
import os

FILE_PATH = "history.json"

def load_history():
    """파일에서 기존 대화 기록을 불러옵니다."""
    if not os.path.exists(FILE_PATH):
        return [] # 파일이 없으면 빈 리스트 반환
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history_list):
    """대화 기록 전체를 파일에 덮어씌워 저장합니다."""
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)
