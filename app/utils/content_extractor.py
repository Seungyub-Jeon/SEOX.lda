import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urlparse
import logging
import chardet
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import socket

# 로깅 설정
logger = logging.getLogger(__name__)

# 다양한 사용자 에이전트 목록
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

def get_random_user_agent():
    """무작위 사용자 에이전트 반환"""
    return random.choice(USER_AGENTS)

def is_binary_content(content_type, content):
    """
    콘텐츠가 바이너리인지 여부를 확인
    
    Args:
        content_type (str): 콘텐츠 유형 헤더 값
        content (bytes): 응답 콘텐츠
        
    Returns:
        bool: 바이너리 콘텐츠 여부
    """
    # 일반적인 텍스트 기반 콘텐츠 타입
    text_types = [
        'text/', 'application/json', 'application/xml', 
        'application/javascript', 'application/xhtml+xml'
    ]
    
    # 콘텐츠 타입으로 확인
    if content_type and any(text_type in content_type.lower() for text_type in text_types):
        return False
        
    # 제대로 디코딩 가능한지 확인
    try:
        # NULL 바이트 검사
        if b'\x00' in content[:1000]:
            return True
            
        # 일반적인 바이너리 파일 시그니처 확인
        binary_signatures = [
            b'\x1f\x8b',  # gzip
            b'\x42\x5a',  # bzip2
            b'\x50\x4b',  # zip
            b'\x89\x50',  # png
            b'\xff\xd8',  # jpeg
            b'\x47\x49',  # gif
            b'\x25\x50',  # pdf
        ]
        
        for sig in binary_signatures:
            if content.startswith(sig):
                return True
                
        # 텍스트로 디코딩 해보기
        content[:100].decode('utf-8')
        return False
    except UnicodeDecodeError:
        # UTF-8 디코딩 실패 시 다른 인코딩 탐지
        detection = chardet.detect(content[:1000])
        if detection['confidence'] > 0.7:
            try:
                content[:100].decode(detection['encoding'])
                return False
            except (UnicodeDecodeError, LookupError):
                return True
        return True

def is_port_in_use(port):
    """지정된 포트가 사용 중인지 확인"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def extract_with_selenium(url, timeout=30):
    """
    Selenium을 사용하여 JavaScript가 필요한 웹사이트에서 콘텐츠 추출
    
    Args:
        url (str): 추출할 웹페이지 URL
        timeout (int): 페이지 로드 타임아웃(초)
        
    Returns:
        str: 추출된 텍스트 또는 None
    """
    driver = None
    try:
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 헤드리스 모드
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # 가용 포트 찾기 (드라이버 통신용)
        port = 9515
        while is_port_in_use(port) and port < 9615:
            port += 1
        
        # 서비스 객체 생성 및 포트 지정
        service = Service(ChromeDriverManager().install(), port=port)
        
        # 드라이버 초기화
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # 사이트 방문
        logger.info(f"Selenium을 사용하여 사이트 방문: {url}")
        driver.get(url)
        
        # 페이지 완전 로드를 위한 대기
        time.sleep(5)
        
        # 스크롤 처리 (필요한 경우)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        
        # 콘텐츠 추출
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 불필요한 요소 제거
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form']):
            element.extract()
        
        # 메인 콘텐츠 영역 찾기
        main_content = None
        content_candidates = [
            soup.find('article'),
            soup.find('main'),
            soup.find(id=re.compile('content|article|main', re.I)),
            soup.find(class_=re.compile('content|article|main|post', re.I)),
            soup.find('div', id=re.compile('content|article|main|post', re.I)),
            soup.find('div', class_=re.compile('content|article|main|post', re.I)),
            soup.body
        ]
        
        # 첫 번째 유효한 요소 선택
        for candidate in content_candidates:
            if candidate:
                main_content = candidate
                break
        
        # 텍스트 추출
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
            
        # 텍스트 정리
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        text = re.sub(r'', '', text)
        
        return text if text and len(text.strip()) > 50 else None
        
    except (TimeoutException, WebDriverException) as e:
        logger.error(f"Selenium 오류 ({url}): {str(e)}")
        return None
    finally:
        # 드라이버 종료
        if driver:
            try:
                driver.quit()
            except:
                pass

def extract_content(search_results):
    """
    검색 결과 URL에서 콘텐츠 추출
    
    Args:
        search_results (list): 검색 결과 사전 목록
        
    Returns:
        list: URL에서 추출한 텍스트 콘텐츠 목록
    """
    extracted_content = []
    
    for result in search_results:
        try:
            url = result['url']
            domain = urlparse(url).netloc
            
            logger.info(f"URL에서 콘텐츠 추출 시도: {url}")
            
            # 헤더 설정 - 크롬 브라우저 에뮬레이션
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # 차단 우회를 위한 Referer 추가 (검색 엔진에서 온 것처럼)
            if 'google.com' not in domain and 'naver.com' not in domain:
                headers['Referer'] = 'https://www.google.com/'
            
            # 한 번만 시도하고 실패하면 건너뜀 (재시도 없음)
            try:
                # URL 콘텐츠 가져오기
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=15,
                    allow_redirects=True
                )
                
                # 403 Forbidden이면 바로 건너뜀
                if response.status_code == 403:
                    logger.warning(f"403 Forbidden 오류 발생: {url} - 건너뜁니다")
                    continue
                
                # 다른 상태 코드 오류면 건너뜀
                if response.status_code != 200:
                    logger.warning(f"HTTP 오류 {response.status_code}: {url} - 건너뜁니다")
                    continue
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"요청 오류 발생: {str(e)} - 건너뜁니다")
                continue
            
            # 콘텐츠 유형 확인
            content_type = response.headers.get('Content-Type', '').lower()
            
            # 바이너리 콘텐츠 확인
            if is_binary_content(content_type, response.content[:4096]):
                logger.warning(f"바이너리 콘텐츠 감지됨: {url} - 건너뜁니다")
                continue
            
            # 인코딩 감지 및 텍스트로 변환
            try:
                if 'charset' in content_type:
                    # 헤더에서 인코딩 정보 추출
                    encoding = re.search(r'charset=([^\s;]+)', content_type).group(1)
                else:
                    # 자동 인코딩 감지
                    detection = chardet.detect(response.content[:4096])
                    encoding = detection['encoding'] if detection['confidence'] > 0.7 else 'utf-8'
                
                # 인코딩 적용하여 텍스트로 변환
                html_content = response.content.decode(encoding, errors='replace')
            except (UnicodeDecodeError, LookupError):
                # 인코딩 오류 시 UTF-8로 시도
                logger.warning(f"인코딩 오류, UTF-8로 시도: {url}")
                html_content = response.content.decode('utf-8', errors='replace')
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 불필요한 요소 제거
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form']):
                element.extract()
                
            # 특정 클래스/ID를 가진 요소 찾기 (메인 콘텐츠일 가능성이 높은 부분)
            main_content = None
            
            # 콘텐츠가 있을 가능성이 높은 요소들 우선순위대로 확인
            content_candidates = [
                soup.find('article'),
                soup.find('main'),
                soup.find(id=re.compile('content|article|main', re.I)),
                soup.find(class_=re.compile('content|article|main|post', re.I)),
                soup.find('div', id=re.compile('content|article|main|post', re.I)),
                soup.find('div', class_=re.compile('content|article|main|post', re.I)),
                soup.body
            ]
            
            # 첫 번째 유효한 요소 선택
            for candidate in content_candidates:
                if candidate:
                    main_content = candidate
                    break
                    
            # 텍스트 추출 및 정리
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
                
            # 줄 단위로 분할하고 앞뒤 공백 제거
            lines = (line.strip() for line in text.splitlines())
            
            # 여러 줄의 제목을 한 줄로 합치기
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # 빈 줄 제거
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # 텍스트 정리: 과도한 공백과 줄바꿈 제거
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            # 특수 문자 및 이상한 유니코드 대체 문자 정리
            text = re.sub(r'[\x00-\x1F\x7F]', '', text)  # 제어 문자 제거
            text = re.sub(r'', '', text)  # 대체 문자 제거
            
            # 결과가 있으면 추가
            if text and len(text.strip()) > 50:  # 최소 텍스트 길이 요구
                logger.info(f"콘텐츠 추출 성공: {url} ({len(text)} 문자)")
                extracted_content.append(text)
            else:
                logger.warning(f"추출된 콘텐츠가 너무 짧거나 비어 있음: {url}")
            
            # 예의 있는 크롤링을 위한 지연 (1-3초 사이 랜덤 지연)
            time.sleep(1 + random.uniform(0, 2))
            
        except Exception as e:
            logger.error(f"콘텐츠 추출 오류 ({result.get('url', '알 수 없는 URL')}): {str(e)}")
            continue
    
    logger.info(f"총 {len(extracted_content)}개 URL에서 콘텐츠 추출 성공")
    return extracted_content