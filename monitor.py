import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import base64
import json

# ===== GitHub Secrets =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")

STATE_FILE = "state.txt"

# ===== 오늘 + 내일 URL =====
def get_urls():
    today = datetime.now()

    tomorrow = today + timedelta(days=1)

    today_url = (
        f"http://www.incheonpilot.com/pilot/pilot04.asp?"
        f"Datepicker_date={today.strftime('%Y-%m-%d')}"
    )

    tomorrow_url = (
        f"http://www.incheonpilot.com/pilot/pilot04.asp?"
        f"Datepicker_date={tomorrow.strftime('%Y-%m-%d')}"
    )

    return [today_url, tomorrow_url]

# ===== 텔레그램 메시지 =====
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=data)

    print("텔레그램 응답:")
    print(response.text)

# ===== GitHub state 읽기 =====
def load_state():
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = response.json()["content"]

        decoded = base64.b64decode(content).decode("utf-8")

        try:
            return json.loads(decoded)
        except:
            return []

    return []

# ===== GitHub state 저장 =====
def save_state(data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    sha = None

    if response.status_code == 200:
        sha = response.json()["sha"]

    content_text = json.dumps(data_list, ensure_ascii=False)

    encoded_content = base64.b64encode(
        content_text.encode("utf-8")
    ).decode("utf-8")

    body = {
        "message": "update state",
        "content": encoded_content,
        "sha": sha
    }

    requests.put(url, headers=headers, json=body)

# ===== 사이트에서 JH 행 감지 =====
def check_page():

    found_rows = []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    urls = get_urls()

    for url in urls:

        response = requests.get(url, headers=headers)

        print(f"페이지 접속 완료: {url}")

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                row_text = row.get_text(" ", strip=True)

                if "JH" in row_text:
                    found_rows.append(row_text)

    print("감지된 JH 행:")
    print(found_rows)

    return found_rows

# ===== 메인 =====
def main():

    old_data = load_state()
    new_data = check_page()

    print("이전 상태:")
    print(old_data)

    print("현재 상태:")
    print(new_data)

    added = [x for x in new_data if x not in old_data]
    removed = [x for x in old_data if x not in new_data]

    # 🚨 새로 추가됨
    if added:

        message = "🚨 JH 추가됨!\n\n"

        for item in added:
            message += f"- {item}\n"

        send_telegram(message)

    # ❌ 삭제됨
    if removed:

        message = "❌ JH 삭제됨!\n\n"

        for item in removed:
            message += f"- {item}\n"

        send_telegram(message)

    # 상태 저장
    save_state(new_data)

if __name__ == "__main__":
    main()
