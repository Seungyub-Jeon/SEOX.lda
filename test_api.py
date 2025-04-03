from serpapi import GoogleSearch
import json
import importlib.util

def test_serpapi_key():
    print("SerpAPI 키 테스트 시작...")
    
    # config.py에서 API 키 가져오기
    try:
        # 프로젝트 루트 경로에서 config.py 로드
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        api_key = getattr(config, "SERPAPI_KEY", "")
        
        if not api_key:
            print("config.py 파일에서 SERPAPI_KEY를 찾을 수 없습니다.")
            return False
            
        print(f"API 키 확인: {api_key[:5]}...")
        
        # 간단한 쿼리로 테스트
        params = {
            "engine": "google",
            "q": "test",
            "api_key": api_key
        }
        
        print("SerpAPI 요청 실행 중...")
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # 응답 확인
        if "error" in results:
            print(f"SerpAPI 오류: {results['error']}")
            return False
        
        if "organic_results" in results:
            num_results = len(results["organic_results"])
            print(f"성공! {num_results}개의 결과를 가져왔습니다.")
            print("첫 번째 결과:", results["organic_results"][0].get("title", ""))
            return True
        else:
            print("응답에 검색 결과가 포함되어 있지 않습니다.")
            print("응답 키:", list(results.keys()))
            return False
            
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_result = test_serpapi_key()
    print("\n결과:", "성공" if test_result else "실패")
    
    if not test_result:
        print("\n권장 조치:")
        print("1. https://serpapi.com에서 등록하여 유효한 API 키를 얻으세요")
        print("2. config.py 파일에 API 키를 올바르게 입력했는지 확인하세요")
        print("3. API 키의 형식은 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'와 같아야 합니다")
        print("4. Google API 키(AIzaSy...로 시작)가 아닌 SerpAPI 키를 사용하세요") 