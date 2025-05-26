import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import matplotlib.pyplot as plt
import pandas as pd
import pathlib
import time

# ChromeDriver 경로
chromedriver_path = "P1/chromedriver.exe"

# WebDriver 설정
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 필요시 헤드리스 모드 활성화
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# WebDriver 초기화
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# 메인 URL
base_url = "https://imtationdarkweb.netlify.app/"

# 결과 저장용 리스트
all_data = []


def crawl_leak_details():
    all_data = []

    try:
        driver.get(base_url)
        time.sleep(3)
        max_pages = 10

        for page_num in range(max_pages):
            try:
                detail_url = f"{base_url}leak-detail/{page_num}"
                driver.get(detail_url)
                time.sleep(2)

                page_source = driver.page_source
                if "Page Not Found" in page_source or "404" in page_source:
                    print(f"{detail_url} - 페이지 없음")
                    continue

                soup = BeautifulSoup(page_source, 'html.parser')
                entries = soup.find_all('div', class_='leaked-entry')

                if not entries:
                    continue

                for entry in entries:
                    personal_info = {}

                    for p in entry.find_all('p'):
                        text = p.get_text(strip=True)

                        if 'Name' in text:
                            personal_info['Name'] = text.split(':')[-1].strip()
                        elif any(k in text for k in ['Phone']):
                            personal_info['Phone'] = text.split(':')[-1].strip()
                        elif any(k in text for k in ['SSN']):
                            personal_info['SSN'] = text.split(':')[-1].replace('-', '').strip()
                        elif any(k in text for k in ['ID']):
                            personal_info['ID'] = text.split(':')[-1].strip()
                        elif any(k in text for k in ['Email']):
                            personal_info['Email'] = text.split(':')[-1].strip()

                    if personal_info:
                        all_data.append(personal_info)

            except Exception as e:
                print(f"페이지 {page_num} 크롤링 중 오류: {e}")
                continue

        # 데이터가 없다면 종료
        if not all_data:
            print("수집된 데이터가 없습니다.")
            return

        # 항목별 리스트 분류
        names = []
        phones = []
        ssns = []
        ids = []
        emails = []

        for item in all_data:
            if 'Name' in item:
                names.append(item['Name'].strip())
            if 'Phone' in item:
                phones.append(item['Phone'].strip())
            if 'SSN' in item:
                ssns.append(item['SSN'].replace('-', '').strip())
            if 'ID' in item:
                ids.append(item['ID'].strip())
            if 'Email' in item:
                emails.append(item['Email'].strip().lower())

        # 중복 제거
        organized_data = {
            'Name': list(set(names)),
            'Phone': list(set(phones)),
            'SSN': list(set(ssns)),
            'ID': list(set(ids)),
            'Email': list(set(emails))
        }

        # JSON 파일 저장
        with open('분류된_개인정보.json', 'w', encoding='utf-8') as f:
            json.dump(organized_data, f, ensure_ascii=False, indent=4)

        print(f"총 {len(all_data)}개의 항목 크롤링 완료 및 분류 저장")

        # JSON 파일 시각화
        # ── 1. Read JSON ────────────────────────────────────────────────────────────
        raw = json.loads(pathlib.Path("분류된_개인정보.json").read_text(encoding="utf-8"))

        # ── 2. Long-format DataFrame ────────────────────────────────────────────────
        df = pd.DataFrame(
            {"Field": field, "Value": value}
            for field, values in raw.items()
            for value in values
        )

        # ── 3-A. Category counts → vertical bar plot (Series.plot.bar) ─────────────
        (df["Field"]
        .value_counts()              # <- returns a Series
        .plot.bar(                   # <- Series.plot.bar
            title="Unique items by PII category",
            xlabel="Category",
            ylabel="Count",
            rot=0,                   # keep tick labels horizontal
            grid=True,               # light grid makes reading easier
            width=0.25,              # bar thickness (0–1 fraction of slot)
        )
        )
        plt.tight_layout()
        plt.show()

        # ── 3-B. E-mail domain counts → horizontal bar plot ────────────────────────
        emails = df.loc[df.Field == "Email", "Value"].str.split("@").str[1]
        (emails
        .value_counts()
        .plot.barh(                  # horizontal variant
            title="E-mail domain distribution",
            xlabel="Count",
            ylabel="Domain",        # 80 % opacity
            alpha=0.8,
            grid=True               
        )
        )
        plt.tight_layout()
        plt.show()


    except Exception as e:
        print(f"전체 크롤링 중 오류 발생: {e}")


# 실행
if __name__ == "__main__":
    try:
        crawl_leak_details()
    finally:
        driver.quit()