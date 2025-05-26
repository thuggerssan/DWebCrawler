import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
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
    try:
        # 메인 페이지 접속
        driver.get(base_url)
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # 최대 크롤링할 페이지 수 (필요에 따라 조절)
        max_pages = 10
        
        # 각 페이지 번호로 직접 접근
        for page_num in range(max_pages):
            try:
                # 개별 leak-detail 페이지 URL 구성
                detail_url = f"{base_url}leak-detail/{page_num}"
                
                # 페이지 접속
                driver.get(detail_url)
                
                # 페이지 로딩 대기
                time.sleep(2)
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                
                # 페이지 존재 여부 확인 (필요시 추가 로직)
                if "Page Not Found" in page_source or "404" in page_source:
                    print(f"{detail_url} - 페이지 없음")
                    continue
                
                # BeautifulSoup으로 파싱
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # leaked-entry 클래스를 가진 div 찾기
                entries = soup.find_all('div', class_='leaked-entry')
                
                print(f"{detail_url} - 발견된 엔트리 수: {len(entries)}")
                
                # 엔트리가 없으면 다음 페이지로
                if not entries:
                    continue
                
                # 각 엔트리 처리
                for entry in entries:
                    personal_info = {}
                    
                    # 각 p 태그에서 정보 추출
                    for p in entry.find_all('p'):
                        # strong 태그 텍스트와 그 다음 텍스트 추출
                        strong = p.find('strong')
                        if strong:
                            key = strong.text.replace(':', '').strip()
                            value = p.get_text(strip=True).replace(strong.text, '').strip()
                            personal_info[key] = value
                    
                    # 데이터가 있으면 리스트에 추가
                    if personal_info:
                        personal_info['source_url'] = detail_url  # 출처 URL 추가
                        all_data.append(personal_info)
                        print(f"추가된 개인정보: {personal_info}")
            
            except Exception as e:
                print(f"페이지 {page_num} 크롤링 중 오류: {e}")
                # 계속 진행
                continue
        
        # JSON 파일로 저장
        if all_data:
            with open('유출된 개인 정보.json', 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"총 {len(all_data)}개의 엔트리 추출 및 저장 완료")
        else:
            print("추출된 데이터가 없습니다.")
    
    except Exception as e:
        print(f"전체 크롤링 중 오류 발생: {e}")

# 스크립트 실행
if __name__ == "__main__":
    try:
        crawl_leak_details()
    finally:
        driver.quit()