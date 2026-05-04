import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import base64

# 🔐 GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")

STATE_FILE = "state.txt"

# ===== 오늘 날짜 URL =====
def get_url():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"http://www.incheonpilot.com/pilot/pilot04.asp?Datepicker_date={today}"

# ===== 텔레그램 전송 =====
def send_telegram(message):
    print("텔레그램 함수 실행됨")

    print("TOKEN:", TELEGRAM_TOKEN)
    print("CHAT_ID:", CHAT_ID)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    res = requests.post(url, data=data)

    print("응답:")
    print(res.text)

# ===== GitHub에서 상태 읽기 =====
def load_state():
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        content = r.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return decoded.strip() == "True"
    else:
        return False

# ===== GitHub에 상태 저장 =====
def save_state(state):
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    r = requests.get(url, headers=headers)
    sha = None

    if r.status_code == 200:
        sha = r.json()["sha"]

    content = base64.b64encode(str(state).encode()).decode()

    data = {
        "message": "update state",
        "content": content,
        "sha": sha
    }

    requests.put(url, headers=headers, json=data)

# ===== 표 안에서 JH 정확 감지 =====
def check_page():
    url = get_url()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all(["td", "th"])

            for col in cols:
                cell_text = col.get_text(strip=True)

                # 🎯 정확히 JH만 감지
                if cell_text == "JH":
                    return True

    return False

# ===== 메인 실행 =====
def main():
    send_telegram("✅ GitHub 테스트 메시지")

    found_before = load_state()
    found_now = check_page()

    # 🚨 새로 생김
    if found_now and not found_before:
        send_telegram("🚨 JH 새로 생성됨!")

    # ❌ 사라짐
    elif not found_now and found_before:
        send_telegram("❌ JH 사라짐!")

    # 상태 저장
    save_state(found_now)

if __name__ == "__main__":
    send_telegram("🔥 GitHub 테스트")
