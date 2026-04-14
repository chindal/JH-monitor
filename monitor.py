import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 🔐 GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

REPO = os.getenv("GITHUB_REPOSITORY")  # 자동 제공됨
STATE_FILE = "state.txt"

# ===== 오늘 날짜 URL =====
def get_url():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"http://www.incheonpilot.com/pilot/pilot04.asp?Datepicker_date={today}"

# ===== 텔레그램 =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ===== GitHub에서 상태 읽기 =====
def load_state():
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        import base64
        content = r.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return decoded.strip() == "True"
    else:
        return False

# ===== GitHub에 상태 저장 =====
def save_state(state):
    import base64

    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # 기존 sha 가져오기
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

# ===== 페이지 확인 =====
def check_page():
    url = get_url()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text()
    return "JH" in text

# ===== 실행 =====
print("모니터링 시작")

def main():
    send_telegram("🔥 테스트 메시지")
    return  # 👈 여기 추가 (강제 종료)
found_before = load_state()
found_now = check_page()

# 🔥 새로 생김
if found_now and not found_before:
    send_telegram("🚨 JH 새로 생성됨!")

# 🔥 사라짐
elif not found_now and found_before:
    send_telegram("❌ JH 사라짐!")

# 상태 저장
save_state(found_now)
