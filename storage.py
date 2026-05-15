# storage.py
import json
import os

def get_file_path(user_id):
    """사용자 ID를 기반으로 고유한 파일 경로를 생성합니다."""
    return f"history_{user_id}.json"

def load_history(user_id):
    """파일에서 기록을 읽어오되, 파일이 없으면 빈 리스트를 반환합니다."""
    file_path = get_file_path(user_id)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(history_list, user_id):
    """기록을 사용자별 고유 파일에 즉시 저장합니다."""
    file_path = get_file_path(user_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

def clear_history(user_id):
    """저장된 특정 사용자의 대화 기록 파일을 삭제합니다."""
    file_path = get_file_path(user_id)
    if os.path.exists(file_path):
        os.remove(file_path)
