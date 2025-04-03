import requests
import importlib.util
import json

def test_google_cse_api():
    """Google Custom Search API 키를 테스트합니다."""
    print("Google Custom Search API 테스트 시작...")
    
    # config.py에서 설정 로드
    try:
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        # API 키와 검색 엔진 ID 가져오기
        api_key = getattr(config, "GOOGLE_API_KEY", "")
        cse_id = getattr(config, "GOOGLE_CSE_ID", "")
        search_api = getattr(config, "SEARCH_API", "serpapi")
        
        print(f"설정에서 검색 API: {search_api}")
        print(f"Google API 키 설정: {'O' if api_key else 'X'}")
        print(f"Google CSE ID 설정: {'O' if cse_id else 'X'}")
        
        if not api_key or api_key == "여기에_당신의_GOOGLE_API_키를_입력하세요":
            print("오류: Google API 키가 설정되지 않았습니다.")
            print("config.py 파일에 GOOGLE_API_KEY를 설정하세요.")
            return
            
        if not cse_id or cse_id == "여기에_당신의_검색엔진_ID를_입력하세요":
            print("오류: Google 검색 엔진 ID가 설정되지 않았습니다.")
            print("config.py 파일에 GOOGLE_CSE_ID를 설정하세요.")
            return
            
        # API 테스트 요청
        query = "test"
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": 3,  # 테스트용으로 3개만 요청
        }
        
        print(f"API 테스트 요청 전송 중: {query} 검색")
        response = requests.get(base_url, params=params)
        data = response.json()
        
        # 응답 확인
        if "error" in data:
            error_msg = data["error"].get("message", "알 수 없는 오류")
            print(f"Google API 오류: {error_msg}")
            print(f"자세한 오류 내용: {json.dumps(data['error'], indent=2)}")
            
            if "Invalid API key" in error_msg:
                print("\n권장 조치:")
                print("1. https://console.cloud.google.com에서 유효한 API 키를 생성하세요.")
                print("2. Custom Search API가 활성화되어 있는지 확인하세요.")
                print("3. API 키에 제한이 없는지 확인하세요 (IP 제한, HTTP 리퍼러 제한 등).")
            
            elif "API key not valid" in error_msg:
                print("\n권장 조치:")
                print("1. 키가 올바른 형식인지 확인하세요.")
                print("2. 키가 활성화되어 있는지 확인하세요.")
                print("3. 키가 Custom Search API에 대한 권한이 있는지 확인하세요.")
                
            elif "Requested entity was not found" in error_msg or "Invalid Value" in error_msg and "cx" in error_msg:
                print("\n권장 조치:")
                print("1. 검색 엔진 ID(cx)가 올바른지 확인하세요.")
                print("2. https://programmablesearchengine.google.com에서 검색 엔진을 생성하고 ID를 확인하세요.")
            
            return
            
        # 검색 결과 확인
        if "items" in data:
            results = data["items"]
            print(f"API 테스트 성공! {len(results)}개의 결과를 받았습니다.")
            print("\n첫 번째 결과:")
            first_result = results[0]
            print(f"제목: {first_result.get('title', '제목 없음')}")
            print(f"URL: {first_result.get('link', 'URL 없음')}")
            print(f"요약: {first_result.get('snippet', '요약 없음')[:100]}...")
        else:
            print("결과가 없거나 응답 형식이 예상과 다릅니다.")
            print(f"응답 데이터: {json.dumps(data, indent=2)[:500]}...")
            
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_google_cse_api() 