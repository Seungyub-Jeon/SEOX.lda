import importlib.util
from app.utils.search import get_search_results
from app.utils.content_extractor import extract_content
from app.utils.topic_modeling import preprocess_text, LDATopicModeler, generate_lda_model
import json
import pprint
import argparse

def debug_search_results(query="검색엔진최적화", language="ko", num_results=10):
    """
    검색 결과를 가져와 분석하고 디버깅 정보를 출력합니다.
    
    Args:
        query (str): 검색 쿼리
        language (str): 언어 코드 ('ko' 또는 'en')
        num_results (int): 가져올 검색 결과 수
    """
    # 1. 검색 결과 가져오기
    print(f"\n[1] '{query}' 검색 결과 가져오기 ({language}, {num_results}개)")
    print("-" * 80)
    
    search_results = get_search_results(query, language, num_results)
    
    print(f"검색 결과 {len(search_results)}개를 가져왔습니다.")
    
    # 검색 결과 세부 정보 출력
    for i, result in enumerate(search_results, 1):
        print(f"\n결과 #{i}:")
        print(f"제목: {result.get('title', '제목 없음')}")
        print(f"URL: {result.get('url', 'URL 없음')}")
        snippet = result.get('snippet', '요약 없음')
        print(f"요약: {snippet[:150]}{'...' if len(snippet) > 150 else ''}")
    
    # 2. 콘텐츠 추출 시도
    print("\n\n[2] 검색 결과에서 콘텐츠 추출")
    print("-" * 80)
    
    content_list = extract_content(search_results[:3])  # 처리 시간 단축을 위해 처음 3개만 처리
    
    print(f"추출된 콘텐츠 {len(content_list)}개")
    
    for i, content in enumerate(content_list, 1):
        print(f"\n콘텐츠 #{i}:")
        content_preview = content[:300].replace('\n', ' ')
        print(f"{content_preview}{'...' if len(content) > 300 else ''}")
        print(f"길이: {len(content)} 문자")
    
    # 3. 텍스트 전처리 및 토큰화
    print("\n\n[3] 콘텐츠 텍스트 전처리 및 토큰화")
    print("-" * 80)
    
    all_tokens = []
    for i, content in enumerate(content_list, 1):
        if not isinstance(content, str) or len(content.strip()) < 50:
            print(f"콘텐츠 #{i}: 전처리 건너뜀 (너무 짧거나 유효하지 않은 콘텐츠)")
            continue
            
        print(f"\n콘텐츠 #{i} 전처리 시작:")
        tokens = preprocess_text(content, language)
        if tokens:
            print(f"토큰화 결과: {len(tokens)}개 토큰")
            print(f"처음 20개 토큰 샘플: {tokens[:20]}")
            all_tokens.extend(tokens)
        else:
            print("토큰화 실패: 결과 없음")
    
    print(f"\n전체 토큰 수: {len(all_tokens)}")
    if all_tokens:
        # 상위 출현 단어 확인
        print("\n가장 많이 출현한 토큰:")
        from collections import Counter
        token_counter = Counter(all_tokens)
        for token, count in token_counter.most_common(20):
            print(f"  - {token}: {count}회")
    
    # 4. 토픽 모델링 수행 (토큰이 충분한 경우)
    if len(all_tokens) >= 10:
        print("\n\n[4] 토픽 모델링 수행")
        print("-" * 80)
        
        num_topics = min(max(2, len(search_results) // 5), 5)  # 결과 수에 따라 주제 수 조정
        print(f"토픽 수: {num_topics}")
        
        try:
            topics = generate_lda_model(all_tokens, num_topics, language)
            print(f"\n추출된 토픽: {len(topics)}개")
            
            # 토픽 출력
            for topic_id, (keywords, weight) in topics.items():
                print(f"\n토픽 {topic_id+1} (가중치: {weight:.2f}):")
                print(f"  키워드: {', '.join(keywords[:10])}")
        except Exception as e:
            print(f"토픽 모델링 오류: {str(e)}")
    else:
        print("\n토큰이 충분하지 않아 토픽 모델링을 건너뜁니다.")
    
    # 5. 결과를 파일로 저장
    print("\n\n[5] 검색 결과와 콘텐츠를 파일로 저장")
    print("-" * 80)
    
    # 검색 결과 저장
    with open("search_results.json", "w", encoding="utf-8") as f:
        json.dump(search_results, f, ensure_ascii=False, indent=2)
    
    # 콘텐츠 저장
    with open("extracted_content.json", "w", encoding="utf-8") as f:
        content_data = [{"url": result.get("url", ""), "content_preview": content[:500]} 
                        for result, content in zip(search_results[:len(content_list)], content_list)]
        json.dump(content_data, f, ensure_ascii=False, indent=2)
    
    print("검색 결과를 'search_results.json' 파일에 저장했습니다.")
    print("추출된 콘텐츠를 'extracted_content.json' 파일에 저장했습니다.")
    
    return search_results, content_list, all_tokens

if __name__ == "__main__":
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='검색 결과 디버깅 도구')
    parser.add_argument('--query', '-q', type=str, default='검색엔진최적화', help='검색 쿼리 (기본값: 검색엔진최적화)')
    parser.add_argument('--language', '-l', type=str, default='ko', choices=['ko', 'en'], help='언어 코드 (ko 또는 en, 기본값: ko)')
    parser.add_argument('--num_results', '-n', type=int, default=10, help='검색 결과 수 (기본값: 10)')
    
    args = parser.parse_args()
    
    # 디버깅 실행
    debug_search_results(query=args.query, language=args.language, num_results=args.num_results) 