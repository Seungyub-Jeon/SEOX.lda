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
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

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

# 추출 제외 도메인 목록
EXCLUDED_DOMAINS = [
    # 학술 사이트
    'scholar.google.com', 'researchgate.net', 'academia.edu', 'kci.go.kr',
    'dbpia.co.kr', 'sciencedirect.com', 'springer.com', 'ieee.org',
    'kiss.kstudy.com', 'koreascience.kr', 'nature.com', 'journal.kci.go.kr',
    'worldcat.org', 'citeseerx.ist.psu.edu', 'tandfonline.com', 'arxiv.org',
    'semanticscholar.org', 'jstor.org', 'kpubs.org', 'ebscohost.com',
    
    # PDF 호스팅 사이트
    'pdfdrive.com', 'scribd.com', 'slideshare.net', 'docsity.com',
    
    # 코드 저장소
    'github.com', 'gitlab.com', 'bitbucket.org', 'stackoverflow.com',
    
    # 기타 텍스트 추출이 어려운 사이트
    'youtube.com', 'vimeo.com', 'dailymotion.com',  # 비디오
    'spotify.com', 'soundcloud.com',  # 오디오
    'instagram.com', 'pinterest.com', 'flickr.com'  # 이미지
]

# 추출 제외 파일 확장자
EXCLUDED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
    '.zip', '.rar', '.tar', '.gz', '.7z',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
    '.mp3', '.mp4', '.avi', '.mov', '.flv', '.wmv',
    '.exe', '.dll', '.iso', '.dmg'
]

def get_random_user_agent():
    """무작위 사용자 에이전트 반환"""
    return random.choice(USER_AGENTS)

def filter_search_results(search_results, max_results=30):
    """
    검색 결과를 필터링하여 콘텐츠 추출이 가능한 URL만 선택
    
    Args:
        search_results (list): 검색 결과 사전 목록
        max_results (int): 처리할 최대 결과 수
        
    Returns:
        list: 필터링된 검색 결과 목록
    """
    filtered_results = []
    skipped_count = 0
    
    for result in search_results:
        # 최대 결과 수 제한
        if len(filtered_results) >= max_results:
            logger.info(f"최대 결과 수 {max_results}개 도달, 필터링 중단")
            break
            
        url = result.get('url', '')
        if not url:
            skipped_count += 1
            continue
            
        # URL 구문 분석
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        
        # 1. 도메인 기반 필터링
        if any(excluded in domain for excluded in EXCLUDED_DOMAINS):
            logger.info(f"제외 도메인으로 건너뜀: {domain} - {url}")
            skipped_count += 1
            continue
            
        # 2. 파일 확장자 기반 필터링
        if any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            logger.info(f"제외 파일 형식으로 건너뜀: {path} - {url}")
            skipped_count += 1
            continue
            
        # 3. URL에 특정 키워드가 포함된 경우 필터링
        exclude_keywords = ['pdf', 'download', 'scholar', 'journal', 'thesis', 
                           'dissertation', 'paper', 'citation', 'citations',
                           'doi', 'isbn', 'issn', 'publication']
        
        if any(keyword in url.lower() for keyword in exclude_keywords):
            logger.info(f"제외 키워드 포함으로 건너뜀: {url}")
            skipped_count += 1
            continue
            
        # 모든 필터 통과
        filtered_results.append(result)
    
    logger.info(f"총 {len(search_results)}개 중 {len(filtered_results)}개 통과, {skipped_count}개 필터링됨")
    return filtered_results

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

def extract_with_selenium(url, timeout=20):
    """
    Selenium을 사용하여 JavaScript가 렌더링된 페이지에서 콘텐츠 추출
    
    Args:
        url (str): 콘텐츠를 추출할 URL
        timeout (int): 페이지 로드 대기 시간(초)
        
    Returns:
        str: 추출된 텍스트 콘텐츠 또는 None
    """
    driver = None
    domain = urlparse(url).netloc
    
    try:
        # Selenium 옵션 설정
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={get_random_user_agent()}')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-notifications')
        options.add_argument('--lang=ko-KR,ko;q=0.9')
        
        # 특정 사이트별 맞춤 설정
        is_special_site = False
        special_selectors = []
        
        # lilys.ai 사이트 맞춤 처리
        if 'lilys.ai' in domain:
            is_special_site = True
            timeout = 25  # 더 긴 대기 시간
            special_selectors = [
                '.note-content', 
                '.note-body', 
                '.content-body',
                '.article__content',
                '.article-content',
                'article',
                '.post-content'
            ]
            logger.info(f"특수 사이트 감지됨: {domain}, 맞춤 처리 적용")
        
        # WebDriver 설정
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(timeout)
        
        # 페이지 로드
        logger.info(f"Selenium으로 URL 접근: {url}")
        driver.get(url)
        
        # 페이지 완전 로드를 위한 대기
        time.sleep(3)  # 기본 대기 시간
        
        # 페이지 스크롤 (동적 로딩 콘텐츠 로드 유도)
        try:
            scroll_height = 300
            for i in range(4):  # 4번 스크롤
                driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                scroll_height += 800
                time.sleep(0.5)
            
            # 페이지 맨 위로 스크롤
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception as e:
            logger.warning(f"스크롤 중 오류: {str(e)}")
        
        # 특수 사이트 맞춤 처리
        if is_special_site and special_selectors:
            for selector in special_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"특수 선택자 매칭됨: {selector}, 요소 {len(elements)}개 발견")
                        combined_text = ' '.join([elem.text for elem in elements if elem.text])
                        if combined_text and len(combined_text) > 200:
                            logger.info(f"특수 선택자를 통한 콘텐츠 추출 성공: {len(combined_text)} 문자")
                            return combined_text
                except Exception as e:
                    logger.warning(f"특수 선택자 '{selector}' 처리 중 오류: {str(e)}")
        
        # 일반 처리
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
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
        
        return text if text and len(text.strip()) > 100 else None
        
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

def evaluate_content_quality(content):
    """
    추출된 콘텐츠의 품질을 평가
    
    Args:
        content (str): 평가할 텍스트 콘텐츠
        
    Returns:
        float: 품질 점수 (0.0 ~ 1.0)
    """
    if not content or len(content) < 100:
        return 0.0
        
    # 점수 계산
    score = 1.0
    
    # 1. 텍스트 길이 체크 (길수록 더 좋음)
    length = len(content)
    if length < 500:
        score *= 0.5
    elif length < 1000:
        score *= 0.7
    elif length < 2000:
        score *= 0.9
    
    # 2. 줄바꿈 비율 확인 (정상 텍스트는 줄바꿈이 적절함)
    newline_ratio = content.count('\n') / max(1, length)
    if newline_ratio > 0.2:  # 줄바꿈이 너무 많음
        score *= 0.7
    elif newline_ratio < 0.01:  # 줄바꿈이 거의 없음
        score *= 0.8
        
    # 3. 특수문자 비율 확인 (너무 높으면 깨진 텍스트 가능성)
    special_char_count = sum(1 for c in content if not c.isalnum() and not c.isspace())
    special_char_ratio = special_char_count / max(1, length)
    if special_char_ratio > 0.3:
        score *= 0.5
    elif special_char_ratio > 0.2:
        score *= 0.7
        
    # 4. 단어 수 확인
    words = content.split()
    word_count = len(words)
    if word_count < 100:
        score *= 0.6
    elif word_count < 200:
        score *= 0.8
    
    # 5. 평균 단어 길이 (너무 길거나 짧으면 의심)
    avg_word_length = sum(len(w) for w in words) / max(1, word_count)
    if avg_word_length > 15 or avg_word_length < 2:
        score *= 0.7
        
    # 6. 인코딩 문제 감지 (깨진 텍스트에 자주 나타나는 패턴)
    encoding_issues = re.findall(r'[\uFFFD\u001A\u001C\u001D\u001E\u001F]', content)
    if len(encoding_issues) > 10:
        score *= 0.5
    elif len(encoding_issues) > 5:
        score *= 0.7
        
    # 7. HTML 태그 감지 (제대로 처리되지 않은 HTML)
    if re.search(r'<[a-zA-Z]+[^>]*>.*?</[a-zA-Z]+>', content):
        score *= 0.7
        
    # 8. 비정상적인 문자 반복 감지
    unusual_repeats = re.findall(r'(.)\1{5,}', content)
    if unusual_repeats:
        score *= 0.8
    
    return max(0.0, min(1.0, score))  # 0.0 ~ 1.0 사이로 제한

def process_url(result):
    """
    단일 URL 처리 함수 - 병렬 처리용
    
    Args:
        result (dict): 처리할 검색 결과 항목
        
    Returns:
        dict or None: 추출 결과가 있으면 결과 사전, 없으면 None
    """
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
        
        # 동적 콘텐츠가 많은 특정 사이트 확인
        is_dynamic_content_site = any(site in domain for site in [
            'lilys.ai', 'tistory.com', 'medium.com', 'velog.io', 'github.io',
            'notion.site', 'substack.com', 'hashnode.com'
        ])
        
        # 특정 동적 사이트는 바로 Selenium으로 처리
        if is_dynamic_content_site:
            logger.info(f"동적 콘텐츠 사이트 감지됨: {domain}, Selenium으로 처리")
            text = extract_with_selenium(url, timeout=25)
            
            if text and len(text.strip()) > 100:
                # 콘텐츠 품질 평가
                quality_score = evaluate_content_quality(text)
                
                # 품질 기준 충족 시 추가 (동적 사이트는 임계값 낮춤)
                threshold = 0.4 if is_dynamic_content_site else 0.5
                
                if quality_score >= threshold:
                    logger.info(f"Selenium 추출 성공: {url} ({len(text)} 문자, 품질 점수: {quality_score:.2f})")
                    return {"url": url, "content": text, "score": quality_score}
                else:
                    logger.warning(f"낮은 품질 콘텐츠 건너뜀: {url} (품질 점수: {quality_score:.2f})")
            else:
                logger.warning(f"Selenium으로 추출된 콘텐츠가 너무 짧거나 비어 있음: {url}")
                
            return None
            
        # 일반 사이트는 requests로 먼저 시도
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
                return None
            
            # 다른 상태 코드 오류면 건너뜀
            if response.status_code != 200:
                logger.warning(f"HTTP 오류 {response.status_code}: {url} - 건너뜁니다")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"요청 오류 발생: {str(e)} - 건너뜁니다")
            return None
        
        # 콘텐츠 유형 확인
        content_type = response.headers.get('Content-Type', '').lower()
        
        # 바이너리 콘텐츠 확인
        if is_binary_content(content_type, response.content[:4096]):
            logger.warning(f"바이너리 콘텐츠 감지됨: {url} - 건너뜁니다")
            return None
        
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
        
        # 품질 평가 및 결과 필터링
        if text and len(text.strip()) > 100:  # 최소 텍스트 길이 요구
            # 콘텐츠 품질 평가
            quality_score = evaluate_content_quality(text)
            
            # 품질 기준 충족 시 추가
            if quality_score >= 0.5:  # 품질 점수 임계값
                logger.info(f"콘텐츠 추출 성공: {url} ({len(text)} 문자, 품질 점수: {quality_score:.2f})")
                return {"url": url, "content": text, "score": quality_score}
            else:
                logger.warning(f"낮은 품질 콘텐츠 건너뜀: {url} (품질 점수: {quality_score:.2f})")
        else:
            # 텍스트가 짧거나 없는 경우 Selenium으로 재시도
            logger.info(f"일반 요청으로 추출 실패, Selenium으로 재시도: {url}")
            text = extract_with_selenium(url)
            
            if text and len(text.strip()) > 100:
                # 콘텐츠 품질 평가
                quality_score = evaluate_content_quality(text)
                
                # 품질 기준 충족 시 추가
                if quality_score >= 0.5:
                    logger.info(f"Selenium 추출 성공: {url} ({len(text)} 문자, 품질 점수: {quality_score:.2f})")
                    return {"url": url, "content": text, "score": quality_score}
                else:
                    logger.warning(f"낮은 품질 콘텐츠 건너뜀: {url} (품질 점수: {quality_score:.2f})")
            else:
                logger.warning(f"추출된 콘텐츠가 너무 짧거나 비어 있음: {url}")
        
        return None
        
    except Exception as e:
        logger.error(f"콘텐츠 추출 오류 ({result.get('url', '알 수 없는 URL')}): {str(e)}")
        return None

def extract_content(search_results):
    """
    검색 결과 URL에서 콘텐츠 추출
    
    Args:
        search_results (list): 검색 결과 사전 목록
        
    Returns:
        list: URL에서 추출한 텍스트 콘텐츠 목록
    """
    # 1. 검색 결과 필터링
    filtered_results = filter_search_results(search_results)
    
    # 병렬 처리를 위한 변수
    max_workers = min(10, len(filtered_results))  # 최대 10개 스레드, 또는 결과 수만큼
    extracted_content = []
    extracted_urls = []  # 추출에 성공한 URL 저장
    
    # 병렬 URL 처리 실행
    logger.info(f"병렬 처리로 {len(filtered_results)}개 URL에서 콘텐츠 추출 시작 (최대 {max_workers} 쓰레드 사용)")
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # URL 처리 작업 제출
        future_to_url = {executor.submit(process_url, result): result for result in filtered_results}
        
        # 완료된 작업 처리 (tqdm으로 진행 상태 표시)
        for future in tqdm(as_completed(future_to_url), total=len(filtered_results), desc="콘텐츠 추출 중"):
            result = future.result()
            if result:
                results.append(result)
    
    # 품질 점수 기준 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 콘텐츠만 추출
    extracted_content = [item["content"] for item in results]
    extracted_urls = [item["url"] for item in results]
    
    # 품질 평가 요약 로깅
    if extracted_content:
        logger.info(f"총 {len(filtered_results)}개 URL 중 {len(extracted_content)}개 콘텐츠 추출 성공")
    else:
        logger.warning("추출된 콘텐츠 없음!")
        
    return extracted_content