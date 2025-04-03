from flask import Blueprint, render_template, request, jsonify, session, send_file, url_for
from app.utils.search import get_search_results
from app.utils.topic_modeling import perform_lda, generate_lda_model, preprocess_text
from app.utils.content_extractor import extract_content
import json
import importlib.util
import traceback
import io
import os
from datetime import datetime
import glob

# 결과 저장 디렉토리 설정
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

main = Blueprint('main', __name__)

def get_api_status():
    """API 키 상태를 확인하고 반환합니다."""
    try:
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        
        # 사용 중인 검색 API 확인
        search_api = getattr(config, "SEARCH_API", "serpapi").lower()
        
        if search_api == "google_cse":
            api_key = getattr(config, "GOOGLE_API_KEY", "")
            cse_id = getattr(config, "GOOGLE_CSE_ID", "")
            
            if not api_key or api_key == "여기에_당신의_GOOGLE_API_키를_입력하세요":
                return {"status": "error", "message": "Google API 키가 설정되지 않았습니다."}
            
            if not cse_id or cse_id == "여기에_당신의_검색엔진_ID를_입력하세요":
                return {"status": "error", "message": "Google 검색 엔진 ID가 설정되지 않았습니다."}
                
            return {"status": "ok", "api": "google_cse"}
        else:
            api_key = getattr(config, "SERPAPI_KEY", "")
            
            if not api_key or api_key == "여기에_당신의_SERPAPI_키를_입력하세요":
                return {"status": "error", "message": "SerpAPI 키가 설정되지 않았습니다."}
                
            return {"status": "ok", "api": "serpapi"}
            
    except Exception as e:
        return {"status": "error", "message": f"설정 파일 로드 중 오류: {str(e)}"}

@main.route('/')
def index():
    api_status = get_api_status()
    return render_template('index.html', api_status=api_status)

@main.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "요청 데이터가 없습니다."}), 400
        
    # API 키 상태 확인
    api_status = get_api_status()
    if api_status["status"] == "error":
        return jsonify({"error": api_status["message"]}), 400
    
    query = data.get('query', '')
    language = data.get('language', 'en')
    
    if not query:
        return jsonify({"error": "검색어가 제공되지 않았습니다."}), 400
    
    print(f"검색 요청 처리 중: 쿼리='{query}', 언어='{language}'")
    
    try:
        # 검색 결과 가져오기 (10개로 제한)
        results = get_search_results(query, language, num_results=40)
        print(f"검색 결과 {len(results)}개를 가져왔습니다.")
        
        if not results:
            if api_status["api"] == "google_cse":
                return jsonify({"error": "Google Custom Search API에서 검색 결과를 가져올 수 없습니다. API 키와 검색 엔진 ID를 확인하세요."}), 500
            else:
                return jsonify({"error": "SerpAPI에서 검색 결과를 가져올 수 없습니다. API 키를 확인하세요."}), 500
        
        # 검색 결과를 JSON 파일로 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f"{query}_{timestamp}"
        search_results_file = os.path.join(RESULTS_DIR, f"{result_filename}_search_results.json")
        
        with open(search_results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 검색 결과에서 콘텐츠 추출
        content_list = extract_content(results)
        print(f"추출된 콘텐츠 길이: {len(content_list)}")
        
        # 추출된 콘텐츠를 JSON 파일로 저장
        content_data = [{"url": result.get("url", ""), "content_preview": content[:500]} 
                       for result, content in zip(results[:len(content_list)], content_list)]
        
        content_file = os.path.join(RESULTS_DIR, f"{result_filename}_extracted_content.json")
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)
        
        if not content_list:
            return jsonify({"error": "검색 결과에서 콘텐츠를 추출할 수 없습니다."}), 500
        
        # 주제 모델링
        num_topics = 5  # 항상 5개 토픽으로 고정
        print(f"LDA 모델링 중... 주제 수: {num_topics}")
        
        # 유효한 콘텐츠만 필터링
        valid_content_list = []
        for content in content_list:
            if isinstance(content, str) and len(content.strip()) > 100:
                valid_content_list.append(content)
        
        # 콘텐츠가 없으면 오류 반환
        if not valid_content_list:
            return jsonify({"error": "유효한 콘텐츠를 추출할 수 없습니다."}), 500
            
        # 각 콘텐츠를 개별적으로 전처리하고 결과 토큰을 합침
        all_tokens = []
        token_analysis = {}
        for i, content in enumerate(valid_content_list):
            try:
                tokens = preprocess_text(content, language)
                if tokens and len(tokens) > 5:  # 최소 토큰 수 확인
                    all_tokens.extend(tokens)
                    # 토큰 빈도 분석 저장
                    token_freq = {}
                    for token in tokens:
                        if token in token_freq:
                            token_freq[token] += 1
                        else:
                            token_freq[token] = 1
                    token_analysis[f"content_{i+1}"] = {
                        "tokens_count": len(tokens),
                        "top_tokens": sorted(token_freq.items(), key=lambda x: x[1], reverse=True)[:20]
                    }
                    print(f"콘텐츠 #{i+1}: {len(tokens)}개 토큰 추출")
                else:
                    print(f"콘텐츠 #{i+1}: 토큰 추출 실패 또는 토큰 부족")
            except Exception as e:
                print(f"콘텐츠 #{i+1} 처리 중 오류: {str(e)}")
        
        print(f"전처리된 텍스트 길이: {len(all_tokens)} 토큰")
        
        # 전체 토큰 빈도 분석
        overall_token_freq = {}
        for token in all_tokens:
            if token in overall_token_freq:
                overall_token_freq[token] += 1
            else:
                overall_token_freq[token] = 1
                
        top_tokens = sorted(overall_token_freq.items(), key=lambda x: x[1], reverse=True)[:50]
        
        # 충분한 토큰이 있는지 확인 (최소 10개)
        if len(all_tokens) < 10:
            return jsonify({"error": "추출된 콘텐츠가 주제 모델링에 충분하지 않습니다."}), 500
        
        # 토픽 모델링 수행 - 무조건 5개 토픽으로 설정
        topics = generate_lda_model(all_tokens, 5, language)
        
        if not topics:
            return jsonify({"error": "주제 모델링을 생성할 수 없습니다."}), 500
            
        print(f"주제 모델링 완료: {len(topics)} 주제")
        
        # 주제 정보 정리
        topic_data = []
        for topic_id, (keywords, weight) in topics.items():
            topic_data.append({
                "id": topic_id,
                "keywords": keywords,
                "weight": weight
            })
        
        # 결과 데이터
        result_data = {
            "query": query,
            "language": language,
            "num_results": len(results),
            "topics": topic_data,
            "token_analysis": {
                "total_tokens": len(all_tokens),
                "top_tokens": top_tokens[:50]
            },
            "timestamp": timestamp,
            "saved_files": {
                "search_results": os.path.basename(search_results_file),
                "extracted_content": os.path.basename(content_file),
                "analysis_result": f"{result_filename}_lda_analysis.json"
            }
        }
        
        # LDA 분석 결과 저장
        analysis_file = os.path.join(RESULTS_DIR, f"{result_filename}_lda_analysis.json")
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        # 세션에 결과 저장 (다운로드용)
        session['last_lda_result'] = result_data
        session['result_filename'] = result_filename
        
        # 결과 반환
        return jsonify(result_data)
        
    except Exception as e:
        print(f"검색 처리 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"검색 처리 중 오류가 발생했습니다: {str(e)}"}), 500

@main.route('/download_lda_results', methods=['GET'])
def download_lda_results():
    """LDA 분석 결과를 JSON 파일로 다운로드합니다."""
    if 'last_lda_result' not in session:
        return jsonify({"error": "다운로드할 분석 결과가 없습니다. 먼저 검색을 실행하세요."}), 404
    
    try:
        # 세션에서 결과 가져오기
        result_data = session['last_lda_result']
        
        # 다운로드할 파일 이름 생성
        query = result_data.get('query', 'search')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"LDA_Analysis_{query}_{timestamp}.json"
        
        # 결과를 JSON으로 직렬화
        result_json = json.dumps(result_data, ensure_ascii=False, indent=2)
        
        # 파일로 반환
        return send_file(
            io.BytesIO(result_json.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"결과 다운로드 중 오류 발생: {str(e)}")
        return jsonify({"error": f"결과 다운로드 중 오류가 발생했습니다: {str(e)}"}), 500

@main.route('/list_saved_results', methods=['GET'])
def list_saved_results():
    """저장된 모든 분석 결과 목록을 반환합니다."""
    try:
        # 디버깅 정보 출력
        print(f"===== 저장된 결과 검색 시작 =====")
        print(f"결과 디렉토리: {RESULTS_DIR}")
        print(f"디렉토리 존재 여부: {os.path.exists(RESULTS_DIR)}")
        
        # 디렉토리 내용 출력
        if os.path.exists(RESULTS_DIR):
            all_files = os.listdir(RESULTS_DIR)
            print(f"디렉토리 내 전체 파일 수: {len(all_files)}")
            print(f"모든 파일 목록: {all_files}")
        
        # 저장된 LDA 분석 파일 검색
        analysis_files = glob.glob(os.path.join(RESULTS_DIR, '*_lda_analysis.json'))
        print(f"LDA 분석 파일 수: {len(analysis_files)}")
        print(f"LDA 분석 파일 목록: {[os.path.basename(f) for f in analysis_files]}")
        
        results = []
        for file_path in analysis_files:
            file_name = os.path.basename(file_path)
            try:
                print(f"파일 처리 중: {file_name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 파일에서 필요한 정보 추출
                query = data.get("query", "알 수 없음")
                language = data.get("language", "ko")
                timestamp = data.get("timestamp", "")
                num_topics = len(data.get("topics", []))
                token_count = data.get("token_analysis", {}).get("total_tokens", 0)
                
                print(f"파일 정보: 쿼리={query}, 언어={language}, 타임스탬프={timestamp}, 토픽 수={num_topics}")
                
                results.append({
                    "filename": file_name,
                    "query": query,
                    "language": language,
                    "timestamp": timestamp,
                    "num_topics": num_topics,
                    "token_count": token_count
                })
            except Exception as e:
                print(f"파일 '{file_path}' 읽기 오류: {str(e)}")
        
        # 날짜/시간 기준으로 정렬 (최신 순)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        print(f"처리된 결과 수: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"결과 #{i+1}: 파일명={result['filename']}, 쿼리={result['query']}, 타임스탬프={result['timestamp']}")
        
        response_data = {"results": results}
        print(f"===== 저장된 결과 검색 완료 =====")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"저장된 결과 목록 조회 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"저장된 결과 목록 조회 중 오류가 발생했습니다: {str(e)}"}), 500

@main.route('/load_saved_result/<filename>', methods=['GET'])
def load_saved_result(filename):
    """저장된 분석 결과를 불러옵니다."""
    try:
        file_path = os.path.join(RESULTS_DIR, filename)
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return jsonify({"error": "요청한 파일을 찾을 수 없습니다."}), 404
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 세션에 저장
        session['last_lda_result'] = data
        
        # 파일명에서 결과 식별자 추출 (타임스탬프 부분)
        parts = filename.split('_lda_analysis.json')[0]
        session['result_filename'] = parts
        
        return jsonify(data)
        
    except Exception as e:
        print(f"저장된 결과 불러오기 중 오류 발생: {str(e)}")
        return jsonify({"error": f"저장된 결과 불러오기 중 오류가 발생했습니다: {str(e)}"}), 500