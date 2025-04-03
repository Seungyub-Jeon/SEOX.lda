import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import os
import sys
import importlib.util
import json
import time

def get_search_results(query, language, num_results=40):
    """
    Get search results from Google for a given query.
    Supports both SerpAPI and Google Custom Search API.
    
    Args:
        query (str): The search query
        language (str): The language code ('en' for English, 'ko' for Korean)
        num_results (int): Number of search results to retrieve
        
    Returns:
        list: List of dictionaries containing search results (url, title, snippet)
    """
    # config.py에서 설정 가져오기
    config = load_config()
    search_api = getattr(config, "SEARCH_API", "serpapi").lower()
    
    # 선택된 API로 검색 수행
    if search_api == "google_cse":
        return get_results_from_google_cse(query, language, num_results, config)
    else:
        return get_results_from_serpapi(query, language, num_results, config)

def load_config():
    """config.py 파일에서 설정 로드"""
    try:
        # 프로젝트 루트 경로에서 config.py 로드
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        return config
    except Exception as e:
        print(f"config.py 파일을 로드하는 중 오류 발생: {str(e)}")
        return type('obj', (object,), {})  # 빈 객체 반환

def get_results_from_google_cse(query, language, num_results, config):
    """Google Custom Search API를 사용하여 검색 결과 가져오기"""
    search_results = []
    
    # API 키와 검색 엔진 ID 가져오기
    api_key = getattr(config, "GOOGLE_API_KEY", "")
    cse_id = getattr(config, "GOOGLE_CSE_ID", "")
    
    # 키가 설정되어 있는지 확인
    if not api_key or not cse_id:
        print("경고: Google Custom Search API 키 또는 CSE ID가 설정되지 않았습니다.")
        print("config.py 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요.")
        return []
    
    print(f"Google Custom Search API 사용 중 (API 키: {api_key[:5]}...)")
    
    # 필요한 페이지 수 계산 (최대 10개 결과/페이지, 최대 10페이지)
    results_per_page = 10
    max_pages = min(min(10, (num_results + results_per_page - 1) // results_per_page), 10)
    
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    for page in range(1, max_pages + 1):
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(results_per_page, 10),  # 최대 10개 결과
            "start": (page - 1) * results_per_page + 1,  # 1-based 인덱스
        }
        
        # 언어 설정
        if language == "ko":
            params["lr"] = "lang_ko"
            params["gl"] = "kr"
        else:
            params["lr"] = "lang_en"
            params["gl"] = "us"
        
        try:
            print(f"페이지 {page} 검색 중...")
            response = requests.get(base_url, params=params)
            data = response.json()
            
            # 에러 확인
            if "error" in data:
                error_msg = data["error"].get("message", "알 수 없는 오류")
                print(f"Google API 오류: {error_msg}")
                break
                
            # 검색 결과 추출
            if "items" in data:
                page_results = data["items"]
                print(f"페이지 {page}에서 {len(page_results)}개의 결과를 찾았습니다.")
                
                for item in page_results:
                    search_results.append({
                        'url': item.get("link", ""),
                        'title': item.get("title", ""),
                        'snippet': item.get("snippet", "")
                    })
                    
                    # 충분한 결과를 얻으면 중단
                    if len(search_results) >= num_results:
                        break
            else:
                print(f"페이지 {page}에서 결과를 찾을 수 없습니다.")
                break
                
            # 다음 페이지로 가기 전 잠시 대기
            if page < max_pages and len(search_results) < num_results:
                time.sleep(1)
                
            # 충분한 결과를 얻었으면 중단
            if len(search_results) >= num_results:
                break
                
        except Exception as e:
            print(f"Google Custom Search API 호출 중 오류 발생: {str(e)}")
            import traceback
            print(traceback.format_exc())
            break
    
    print(f"총 {len(search_results)}개의 검색 결과를 Google Custom Search에서 가져왔습니다.")
    
    # 추가 정보 추출 (필요한 경우)
    enrich_search_results(search_results)
    
    return search_results

def get_results_from_serpapi(query, language, num_results, config):
    """SerpAPI를 사용하여 검색 결과 가져오기"""
    search_results = []
    
    # SerpAPI 키 가져오기
    api_key = getattr(config, "SERPAPI_KEY", "")
    
    if not api_key or api_key == "여기에_당신의_SERPAPI_키를_입력하세요":
        print("경고: SERPAPI_KEY가 설정되지 않았습니다. config.py 파일에 API 키를 입력하세요.")
        print("SerpAPI에 가입하여 API 키를 얻으세요: https://serpapi.com")
        return []  # API 키가 없으면 빈 결과 반환
    
    print(f"SerpAPI 사용 중 (API 키: {api_key[:5]}...)")
    
    # 각 페이지에서 가져올 결과 수
    results_per_page = 10
    
    # 필요한 페이지 수 계산 (최대 4페이지)
    max_pages = min(4, (num_results + results_per_page - 1) // results_per_page)
    
    for page in range(1, max_pages + 1):
        # 검색 매개변수 설정
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": results_per_page
        }
        
        # 두 번째 페이지부터는 페이지 번호 추가
        if page > 1:
            params["start"] = (page - 1) * results_per_page
        
        # 언어 설정
        if language == "ko":
            params["gl"] = "kr"
            params["hl"] = "ko"
        else:
            params["gl"] = "us"
            params["hl"] = "en"
        
        print(f"페이지 {page} 검색 매개변수: {json.dumps({k: v for k, v in params.items() if k != 'api_key'})}")
        
        try:
            # SerpAPI 검색 실행
            search = GoogleSearch(params)
            results = search.get_dict()
            
            print(f"페이지 {page} SerpAPI 응답 키: {list(results.keys())}")
            
            # 검색 결과 추출
            if "organic_results" in results:
                page_results = results["organic_results"]
                print(f"페이지 {page} 유기적 검색 결과 수: {len(page_results)}")
                
                for result in page_results:
                    url = result.get("link", "")
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    
                    # 중복 검사 (URL 기준)
                    if not any(r.get('url') == url for r in search_results):
                        search_results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet
                        })
                    
                    # 충분한 결과를 얻었으면 중단
                    if len(search_results) >= num_results:
                        break
            else:
                print(f"페이지 {page} SerpAPI 응답에 'organic_results' 키가 없습니다.")
                if "error" in results:
                    print(f"SerpAPI 오류: {results['error']}")
                else:
                    print(f"응답 데이터: {json.dumps(results, indent=2)[:500]}...")
            
            # 다음 페이지 결과를 가져오기 전에 잠시 대기 (API 속도 제한 방지)
            if page < max_pages and len(search_results) < num_results:
                print(f"다음 페이지를 가져오기 전 2초 대기...")
                time.sleep(2)
            
            # 충분한 결과를 얻었거나 응답에 결과가 없으면 더 이상 요청하지 않음
            if len(search_results) >= num_results or "organic_results" not in results or not results["organic_results"]:
                break
                
        except Exception as e:
            print(f"페이지 {page} 검색 중 오류 발생: {str(e)}")
            import traceback
            print(traceback.format_exc())
            # 오류 발생 시 다음 페이지로 진행
            continue
    
    print(f"총 {len(search_results)}개의 검색 결과를 SerpAPI에서 가져왔습니다.")
    
    # 추가 정보 추출
    enrich_search_results(search_results)
    
    return search_results

def enrich_search_results(search_results):
    """검색 결과에서 추가 정보 추출"""
    if not search_results:
        return
        
    print("URL에서 추가 정보 추출 중...")
    
    # 더 많은 정보가 필요하면 URL에서 추가 데이터 추출
    for i, result in enumerate(search_results):
        try:
            if not result['snippet'] or len(result['snippet']) < 50:
                print(f"URL {i+1}/{len(search_results)}에서 추가 정보 추출 중: {result['url'][:50]}...")
                response = requests.get(result['url'], timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 메타 설명에서 스니펫 추출 시도
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and 'content' in meta_desc.attrs:
                    result['snippet'] = meta_desc['content']
                else:
                    first_p = soup.find('p')
                    if first_p:
                        result['snippet'] = first_p.get_text()
                
                # 스니펫이 너무 길면 자름
                if len(result['snippet']) > 200:
                    result['snippet'] = result['snippet'][:200] + '...'
        except Exception as e:
            print(f"URL 처리 중 오류 발생 {result['url'][:30]}: {str(e)}")
            continue