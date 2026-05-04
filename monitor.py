import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import base64
import json
import time
import hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ===== GitHub Secrets =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")

STATE_FILE = "state.txt"

BASE_URL = "http://www.incheonpilot.com/pilot/pilot04.asp"

# ===== 텔레그램 =====
def send_telegram(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=data)

    print("텔레그램 응답:")
    print(response.text)

# ===== 오늘 / 내일 URL =====
def get_urls():

    today = datetime.now()

    tomorrow = today + timedelta(days=1)

    return [
        today.strftime("%Y-%m-%d"),
        tomorrow.strftime("%Y-%m-%d")
    ]

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
            return {}

    return {}

# ===== GitHub state 저장 =====
def save_state(data):

    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    sha = None

    if response.status_code == 200:
        sha = response.json()["sha"]

    content_text = json.dumps(data, ensure_ascii=False)

    encoded_content = base64.b64encode(
        content_text.encode("utf-8")
    ).decode("utf-8")

    body = {
        "message": "update state",
        "content": encoded_content,
        "sha": sha
    }

    requests.put(url, headers=headers, json=body)

# ===== Selenium 브라우저 =====
def create_driver():

    options = Options()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    return driver

# ===== 페이지 검사 =====
def check_page():

    results = {}

    driver = create_driver()

    try:

        dates = get_urls()

        for date_str in dates:

            url = (
                f"{BASE_URL}"
                f"?Datepicker_date={date_str}"
            )

            print(f"접속 중: {date_str}")

            driver.get(url)

            time.sleep(5)

            html = driver.page_source

            soup = BeautifulSoup(html, "html.parser")

            tables = soup.find_all("table")

            matched_html = ""

            for table in tables:

                table_html = str(table)

                if "JH" in table_html:
                    matched_html += table_html

            if matched_html:

                html_hash = hashlib.md5(
                    matched_html.encode()
                ).hexdigest()

                results[date_str] = html_hash

                print(f"{date_str} → JH 발견")

            else:

                print(f"{date_str} → JH 없음")

    finally:

        driver.quit()

    return results

# ===== 메인 =====
def main():

    old_state = load_state()

    new_state = check_page()

    print("이전 상태:")
    print(old_state)

    print("현재 상태:")
    print(new_state)

    added_dates = []
    changed_dates = []
    removed_dates = []

    # 새로 생김 / 변경
    for date_key, new_hash in new_state.items():

        if date_key not in old_state:

            added_dates.append(date_key)

        elif old_state[date_key] != new_hash:

            changed_dates.append(date_key)

    # 삭제
    for date_key in old_state:

        if date_key not in new_state:

            removed_dates.append(date_key)

    # ===== 새로 생성 =====
    if added_dates:

        message = "🚨 JH 새로 생성됨\n"

        for d in added_dates:
            message += f"\n\n📅 {d}"

        send_telegram(message)

    # ===== 변경 =====
    if changed_dates:

        message = "🔄 JH 변경 감지\n"

        for d in changed_dates:
            message += f"\n\n📅 {d}"

        send_telegram(message)

    # ===== 삭제 =====
    if removed_dates:

        message = "❌ JH 삭제됨\n"

        for d in removed_dates:
            message += f"\n\n📅 {d}"

        send_telegram(message)

    # 상태 저장
    save_state(new_state)

if __name__ == "__main__":
    main()
