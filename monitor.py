import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import base64
import json
import time
import hashlib
from zoneinfo import ZoneInfo

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

    korea_time = datetime.now(
        ZoneInfo("Asia/Seoul")
    )

    tomorrow = korea_time + timedelta(days=1)

    return [
        korea_time.strftime("%Y-%m-%d"),
        tomorrow.strftime("%Y-%m-%d")
    ]

# ===== GitHub state 읽기 =====
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

# ===== GitHub state 저장 =====
def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("state.txt 파일 로컬 저장 완료")

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
            url = f"{BASE_URL}?Datepicker_date={date_str}"
            print(f"접속 중: {date_str}")

            driver.get(url)
            driver.refresh()
            
            # 페이지 로딩을 위해 잠시 대기
            time.sleep(10)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # --- 이 부분이 수정된 핵심 로직입니다 ---
            matched_content = ""
            rows = soup.find_all("tr") # 모든 행(줄)을 가져옴

            for row in rows:
                # 줄바꿈과 공백을 정리하고 텍스트만 추출
                row_text = row.get_text(separator="|", strip=True)

                if "JH" in row_text:
                    # JH가 포함된 줄의 글자 정보만 차곡차곡 쌓음
                    matched_content += row_text + "\n"

            if matched_content:
                # 깨끗하게 걸러진 '글자 데이터'만 가지고 해시 생성
                html_hash = hashlib.md5(
                    matched_content.encode('utf-8')
                ).hexdigest()

                results[date_str] = html_hash
                print(f"{date_str} → JH 데이터 추출 성공")
            else:
                print(f"{date_str} → JH 없음")
            # --------------------------------------

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

    # ===== 최초 감지 =====
    if added_dates:

        message = "🚨 JH 최초 감지\n"

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
