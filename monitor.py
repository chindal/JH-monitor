import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import base64
import json
import time

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

    found_rows = []

    driver = create_driver()

    try:

        driver.get(BASE_URL)

        time.sleep(3)

        dates = [
            datetime.now(),
            datetime.now() + timedelta(days=1)
        ]

        for target_date in dates:

            date_str = target_date.strftime("%Y-%m-%d")

            print(f"검사 날짜: {date_str}")

            # 날짜 입력칸 찾기
            date_input = driver.find_element(By.NAME, "Datepicker_date")

            # 기존 값 삭제
            date_input.clear()

            # 날짜 입력
            date_input.send_keys(date_str)

            # 엔터 대신 JS submit
            driver.execute_script("document.forms[0].submit();")

            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            tables = soup.find_all("table")

            for table in tables:

                rows = table.find_all("tr")

                for row in rows:

                    row_text = row.get_text(" ", strip=True)

                    if "JH" in row_text:

                        full_text = f"[{date_str}] {row_text}"

                        found_rows.append(full_text)

        print("감지 결과:")
        print(found_rows)

    finally:

        driver.quit()

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

    # 🚨 새로 추가
    if added:

        message = "🚨 JH 추가됨!\n\n"

        for item in added:
            message += f"- {item}\n"

        send_telegram(message)

    # ❌ 삭제
    if removed:

        message = "❌ JH 삭제됨!\n\n"

        for item in removed:
            message += f"- {item}\n"

        send_telegram(message)

    # 상태 저장
    save_state(new_data)

if __name__ == "__main__":
    main()
