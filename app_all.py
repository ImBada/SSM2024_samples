import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 캡처 대상 URL
capture_urls = [
    "https://localhost:5010/ui/16x9_1P",
    "https://localhost:5010/ui/4x3_1P",
    "https://localhost:5010/ui/4x1_1P"
]

# POST 요청 보낼 URL
post_url = "https://localhost:5010/api/run/"

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
drivers = [webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) for _ in capture_urls]
for driver in drivers:
    driver.set_window_size(desired_width, desired_height)

def post_request_and_capture():
    id_counter = 1

    while True:
        try:
            # POST 요청
            payload = id_counter
            response = requests.post(post_url, json=payload, verify=False)
            print(f"POST 요청 보냄 (id={id_counter}): {response.status_code}, {response.text}")
            if response.status_code != 200:
                break

            # 폴더 생성
            folder_name = f"id_{id_counter}"
            os.makedirs(folder_name, exist_ok=True)
            print(f"폴더 생성됨: {folder_name}")
            time.sleep(0.3)  # 페이지 렌더링 대기

            # 캡처 작업 (각 드라이버에서 렌더링된 화면 캡처)
            for idx, driver in enumerate(drivers):
                screenshot_path = os.path.join(folder_name, f"screenshot_{idx + 1}.png")
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
        for idx, driver in enumerate(drivers):
            driver.get(capture_urls[idx])

        post_request_and_capture()
    finally:
        # 모든 WebDriver 종료
        for driver in drivers:
            driver.quit()