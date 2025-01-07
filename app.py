import os
import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 캡처 대상 URL
capture_urls = {
    "RUN_16:9_1P": "https://badagames.asuscomm.com:5173/ui/16x9_1P",
    "RUN_16:9_2P_COOP": "https://badagames.asuscomm.com:5173/ui/16x9_2P",
    "RUN_4:3_1P": "https://badagames.asuscomm.com:5173/ui/4x3_1P",
    "RUN_16:9_2P_VS": "https://badagames.asuscomm.com:5173/ui/16x9_2P_VS"
}

# POST 요청 보낼 URL
post_url = "https://badagames.asuscomm.com:5173/api/run/"

# CSV 파일 URL
load_dotenv()
csv_url = os.getenv("CSV_URL")
if not csv_url:
    raise ValueError("CSV_URL 환경 변수가 설정되지 않았습니다.")

desired_width = 1920
desired_height = 1080 + 139  # 139: 브라우저 상단바 높이

# WebDriver 설정
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # 브라우저 UI 표시 안 함
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--hide-scrollbars")

# WebDriver 인스턴스를 URL마다 생성
drivers = {key: webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) for key in capture_urls}
for driver in drivers.values():
    driver.set_window_size(desired_width, desired_height)

def fetch_csv_data():
    """CSV 파일 다운로드 및 파싱"""
    response = requests.get(csv_url)
    response.raise_for_status()
    
    # CSV 데이터를 파싱
    csv_data = []
    decoded_content = response.content.decode('utf-8')
    csv_reader = csv.DictReader(decoded_content.splitlines())
    for row in csv_reader:
        csv_data.append({"id": row["id"], "sceneName": row["sceneName"]})
    return csv_data

def post_request_and_capture(csv_data):
    id_counter = 1

    folder_name = f"results"
    os.makedirs(folder_name, exist_ok=True)

    for entry in csv_data:
        try:
            # POST 요청
            payload = id_counter
            response = requests.post(post_url, json=payload, verify=False)
            print(f"POST 요청 보냄 (id={id_counter}): {response.status_code}, {response.text}")
            if response.status_code != 200:
                break

            time.sleep(0.3)  # 페이지 렌더링 대기

            page = entry["sceneName"]
            if page in capture_urls:
                # 해당 페이지만 캡처
                driver = drivers[page]
                screenshot_path = os.path.join(folder_name, f"{id_counter}-layout.png")
                driver.save_screenshot(screenshot_path)
                print(f"캡처 완료: {screenshot_path}")

            # 대기 시간
            id_counter += 1

        except Exception as e:
            print(f"오류 발생: {e}")
            break

if __name__ == "__main__":
    try:
        # 각 드라이버로 URL 로드 (처음 한 번만 실행)
        for page, driver in drivers.items():
            driver.get(capture_urls[page])

        # CSV 데이터 가져오기
        csv_data = fetch_csv_data()
        print(f"CSV 데이터 로드 완료: {csv_data}")

        # POST 요청 및 캡처 실행
        post_request_and_capture(csv_data)
    finally:
        # 모든 WebDriver 종료
        for driver in drivers.values():
            driver.quit()