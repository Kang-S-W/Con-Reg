import json
import os

# 기록을 저장할 파일 이름
FILE_PATH = "history.json"

def load_history():
    """
    [불러오기] 파일에서 전체 대화 기록을 가져옵니다.
    처음 실행하거나 기록이 없으면 빈 리스트를 반환합니다.
    """
    if not os.path.exists(FILE_PATH):
        return []
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history_list):
    """
    [저장하기] 새로운 대화가 추가되거나 삭제될 때, 
    업데이트된 전체 기록을 파일에 덮어씌워 영구 저장합니다.
    """
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

def get_history_item(index):
    """
    [열람 기능용] 전체 기록 중 사용자가 클릭한 특정 순서(index)의 
    기록 하나만 정확하게 뽑아서 반환합니다.
    """
    history = load_history()
    if 0 <= index < len(history):
        return history[index]
    return None

def clear_history():
    """
    [삭제 기능용] 모든 기록을 지우고 빈 파일로 초기화합니다.
    """
    save_history([])
