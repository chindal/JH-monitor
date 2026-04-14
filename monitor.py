import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json

# ===== 환경 변수 (GitHub Secrets) =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

# ===== URL =====
def get_url():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"http://www.incheonpilot.com/pilot/pilot04.asp?Datepicker_date={today}"

# ===== 텔레그램 =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ===== 상태 불러오기 =====
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": "", "data": []}

# ===== 상태 저장 =====
def save_state(date, data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": date, "data": data}, f, ensure_ascii=False)

# ===== JH 추출 (표 기준 정확 탐지) =====
def get_jh_list():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(get_url(), headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    result = []

    rows = soup.find_all("tr")

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]

        # 👉 데이터 행만 필터 + JH 포함 행만
        if len(cols) > 3 and "JH" in cols:
            result.append(" | ".join(cols))

    return sorted(result)

# ===== 메인 =====
def main():
    state = load_state()

    today = datetime.now().strftime("%Y-%m-%d")
    prev_date = state["date"]
    prev_jh = state["data"]

    current_jh = get_jh_list()

    # ✅ 날짜 바뀌면 초기화 (오탐 방지 핵심)
    if today != prev_date:
        print(f"📅 날짜 변경 감지: {prev_date} → {today}")
        prev_jh = []

    # ✅ 변화 감지
    added = [j for j in current_jh if j not in prev_jh]
    removed = [j for j in prev_jh if j not in current_jh]

    # ✅ 알림
    if added:
        send_telegram(f"🚨 {today} JH 추가:\n" + "\n".join(added))
        print("추가:", added)

    if removed:
        send_telegram(f"❌ {today} JH 삭제:\n" + "\n".join(removed))
        print("삭제:", removed)

    # ✅ 상태 저장
    save_state(today, current_jh)

# ===== 실행 =====
if __name__ == "__main__":
    main()
