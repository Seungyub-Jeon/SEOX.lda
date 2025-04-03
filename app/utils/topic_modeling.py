from gensim import corpora, models
import pyLDAvis
import pyLDAvis.gensim_models
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
import json
from konlpy.tag import Okt
import numpy as np
from nltk.stem import WordNetLemmatizer
from collections import defaultdict
import logging
import os

# Download required NLTK data
nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')
if not os.path.exists(os.path.join(nltk_data_path, 'corpora', 'stopwords')):
    print("NLTK 데이터 다운로드 중...")
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)

# 로거 설정
logger = logging.getLogger(__name__)

class LDATopicModeler:
    def __init__(self, language='en'):
        self.language = language
        self.stopwords = set(stopwords.words('english'))
        self.tokenizer = word_tokenize
        
        # Set up Korean processor if needed
        if language == 'ko':
            self.okt = Okt()
            # Korean stopwords (common words that don't add meaning)
            self.stopwords = {'이', '그', '저', '것', '이것', '저것', '그것', '및', '에', '에서', 
                              '의', '을', '를', '이런', '그런', '와', '과', '은', '는', '이나', 
                              '나', '또는', '혹은', '등', '들'}
    
    def preprocess_text(self, texts):
        processed_texts = []
        
        for text in texts:
            if not text or len(text.strip()) < 10:
                continue  # 너무 짧은 텍스트는 건너뜀
                
            if self.language == 'en':
                # Tokenize, lowercase, remove stopwords and short words
                tokens = self.tokenizer(text.lower())
                tokens = [token for token in tokens if token.isalpha() and token not in self.stopwords and len(token) > 1]
            
            elif self.language == 'ko':
                # Use Okt for Korean text processing
                tokens = self.okt.nouns(text)  # Extract nouns which are most meaningful for topics
                tokens = [token for token in tokens if token not in self.stopwords and len(token) > 1]
            
            if tokens:
                processed_texts.append(tokens)
        
        print(f"전처리 후 텍스트 수: {len(processed_texts)}")
        if processed_texts:
            print(f"첫 번째 텍스트 토큰 예시 (최대 10개): {processed_texts[0][:10]}")
            print(f"토큰이 있는 텍스트의 평균 토큰 수: {sum(len(text) for text in processed_texts) / len(processed_texts):.1f}")
            
        return processed_texts
    
    def generate_lda_model(self, processed_texts, num_topics=5):
        # 데이터가 너무 적으면 토픽 수 조정
        if len(processed_texts) < 5:
            print(f"경고: 데이터가 너무 적습니다. 토픽 수를 {num_topics}에서 2로 줄입니다.")
            num_topics = 2
        elif len(processed_texts) < 10:
            print(f"경고: 데이터가 적습니다. 토픽 수를 {num_topics}에서 3으로 줄입니다.")
            num_topics = 3
        
        # Create dictionary
        dictionary = corpora.Dictionary(processed_texts)
        
        # 원래 필터링 기준
        # dictionary.filter_extremes(no_below=2, no_above=0.9)
        
        # 데이터 수가 적을 때는 필터링 기준 완화
        if len(processed_texts) < 10:
            # 적은 수의 문서에서는 필터링을 최소화
            dictionary.filter_extremes(no_below=1, no_above=0.95)
            print("소량 데이터 처리: 필터링 기준 완화됨 (no_below=1, no_above=0.95)")
        else:
            # 일반적인 경우 조금 완화된 필터링 적용
            dictionary.filter_extremes(no_below=1, no_above=0.9)
            print("필터링 기준 약간 완화됨 (no_below=1, no_above=0.9)")
        
        print(f"필터링 후 단어 사전 크기: {len(dictionary)}")
        
        # 사전이 너무 작으면 경고
        if len(dictionary) < 10:
            print("경고: 필터링 후 단어가 너무 적습니다!")
        
        # Convert to bag of words
        corpus = [dictionary.doc2bow(text) for text in processed_texts]
        
        print(f"코퍼스 크기: {len(corpus)}")
        
        # 빈 코퍼스 체크
        if not corpus or not any(corpus):
            raise ValueError("처리된 텍스트에서 단어를 찾을 수 없습니다. 데이터를 확인하세요.")
        
        # Train LDA model (LDA는 최소한 몇 개의 단어라도 있으면 돌아갑니다)
        lda_model = models.LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            passes=15,  # 적은 데이터에서는 passes 증가
            iterations=50,
            alpha='auto',
            per_word_topics=True
        )
        
        return lda_model, corpus, dictionary
    
    def generate_visualization(self, lda_model, corpus, dictionary):
        # 코퍼스가 너무 작으면 시각화 건너뜀
        if len(corpus) < 3:
            return "데이터가 부족하여 시각화를 생성할 수 없습니다."
            
        try:
            # Generate interactive visualization
            vis_data = pyLDAvis.gensim_models.prepare(lda_model, corpus, dictionary)
            
            # Convert to JSON for web display
            vis_json = pyLDAvis.prepared_data_to_html(vis_data)
            
            return vis_json
        except Exception as e:
            print(f"시각화 생성 중 오류 발생: {str(e)}")
            return "시각화를 생성하는 중 오류가 발생했습니다."
    
    def format_topics(self, lda_model, num_words=10):
        topics = []
        
        for topic_id, topic_words in lda_model.print_topics(num_words=num_words):
            # Extract words and their weights
            words_with_weights = re.findall(r'"([^"]+)"\*(\d+\.\d+)', topic_words)
            
            # 결과가 없으면 다른 정규식 패턴 시도
            if not words_with_weights:
                words_with_weights = re.findall(r'([^\s"*]+)\*(\d+\.\d+)', topic_words)
            
            # Format as a list of dictionaries with word and weight
            formatted_words = [
                {"word": word, "weight": float(weight)}
                for word, weight in words_with_weights
            ]
            
            topics.append({
                "id": topic_id,
                "words": formatted_words
            })
        
        return topics

def preprocess_text(text, language='en'):
    """
    텍스트를 전처리하고 토큰화합니다.
    
    Args:
        text (str 또는 list): 전처리할 텍스트 또는 텍스트 목록
        language (str): 언어 코드 ('en' 또는 'ko')
        
    Returns:
        list: 토큰화된 단어 목록
    """
    logger.info(f"텍스트 전처리 시작: 언어={language}")
    
    # text가 리스트인 경우 처리 (첫 번째 유효한 문자열만 사용)
    if isinstance(text, list):
        logger.warning(f"리스트 입력을 받았습니다. 첫 번째 유효한 항목만 처리합니다.")
        
        # 리스트에서 첫 번째 유효한 문자열 찾기
        valid_text = None
        for item in text:
            if isinstance(item, str) and len(item.strip()) > 50:  # 최소 길이 체크
                valid_text = item
                break
                
        if valid_text is None:
            logger.warning("리스트에서 유효한 문자열을 찾을 수 없습니다.")
            return []
            
        text = valid_text
    
    # text가 문자열이 아닌 경우 처리
    if not isinstance(text, str):
        logger.warning(f"텍스트가 문자열이 아닙니다: {type(text)}")
        return []
    
    # 빈 문자열 또는 너무 짧은 텍스트 체크
    if not text or len(text.strip()) < 10:
        logger.warning("텍스트가 너무 짧습니다.")
        return []
    
    # 언어에 따라 적절한 전처리 함수 호출
    if language == 'ko':
        return preprocess_korean(text)
    else:
        return preprocess_english(text)

def preprocess_korean(text):
    """한국어 텍스트 전처리"""
    try:
        # 항상 Okt 사용 (MeCab 사용하지 않음)
        okt = Okt()
        
        # 텍스트 정규화
        # 소문자 변환은 한국어에 적용할 필요 없으나, 혼합 텍스트가 있을 수 있어서 유지
        text = text.lower() if hasattr(text, 'lower') else text
        text = re.sub(r'[^\w\s]', ' ', text)  # 문장부호 제거
        text = re.sub(r'\s+', ' ', text).strip()  # 여러 공백을 하나로 변환
        
        # 명사 추출 (Okt 사용)
        nouns = okt.nouns(text)
        
        # 한글자 단어 필터링 (선택적)
        filtered_words = [w for w in nouns if len(w) > 1]
        
        # 불용어 제거 (한국어 불용어 목록은 필요에 따라 추가)
        ko_stop_words = set(['있다', '하다', '되다', '이다', '돌다', '보다', '않다', '이렇다', '그렇다', '어떻다'])
        result = [w for w in filtered_words if w not in ko_stop_words]
        
        logger.info(f"한국어 전처리 완료: {len(result)} 토큰 생성")
        return result
        
    except Exception as e:
        logger.error(f"한국어 전처리 중 오류 발생: {str(e)}")
        # 오류 발생 시 빈 목록 반환하지 않고 최소한의 처리된 텍스트 반환
        try:
            # 간단한 공백 기반 토큰화로 대체
            simple_tokens = re.sub(r'[^\w\s]', ' ', text.lower() if hasattr(text, 'lower') else str(text)).split()
            filtered = [w for w in simple_tokens if len(w) > 1]
            logger.info(f"간단한 토큰화로 대체: {len(filtered)} 토큰")
            return filtered
        except:
            logger.error("대체 처리도 실패")
            return []

def preprocess_english(text):
    """영어 텍스트 전처리"""
    try:
        # 텍스트 정규화
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # 문장부호 제거
        text = re.sub(r'\s+', ' ', text).strip()  # 여러 공백을 하나로 변환
        
        # 토큰화
        tokens = word_tokenize(text)
        
        # 불용어 제거
        stop_words = set(stopwords.words('english'))
        filtered_words = [w for w in tokens if w not in stop_words and len(w) > 2]
        
        # 표제어 추출
        lemmatizer = WordNetLemmatizer()
        lemmatized = [lemmatizer.lemmatize(w) for w in filtered_words]
        
        logger.info(f"영어 전처리 완료: {len(lemmatized)} 토큰 생성")
        return lemmatized
        
    except Exception as e:
        logger.error(f"영어 전처리 중 오류 발생: {str(e)}")
        # 오류 발생 시 간단한 처리로 대체
        try:
            # 간단한 공백 기반 토큰화로 대체
            simple_tokens = re.sub(r'[^\w\s]', ' ', text.lower()).split()
            filtered = [w for w in simple_tokens if len(w) > 2 and w not in set(stopwords.words('english'))]
            logger.info(f"간단한 토큰화로 대체: {len(filtered)} 토큰")
            return filtered
        except:
            logger.error("대체 처리도 실패")
            return []

def generate_lda_model(tokens, num_topics=5, language='en'):
    """
    LDA 토픽 모델링을 수행합니다.
    
    Args:
        tokens (list): 전처리된 토큰 리스트
        num_topics (int): 추출할 토픽 수
        language (str): 텍스트 언어 ('en' 또는 'ko')
        
    Returns:
        dict: 토픽 ID를 키로, (키워드 리스트, 가중치)를 값으로 하는 딕셔너리
    """
    if not tokens:
        logger.warning("토큰이 없어 LDA 모델을 생성할 수 없습니다.")
        return {}
        
    try:
        # 토픽 수를 기본 5개로 설정하고 토큰이 적을 때만 조정
        token_count = len(tokens)
        orig_num_topics = num_topics
        
        if token_count < 100:
            # 토큰이 매우 적은 경우에만 토픽 수 조정
            if token_count < 30:
                num_topics = min(2, num_topics)
                logger.warning(f"토큰 수({token_count})가 적어 토픽 수를 {num_topics}로 조정합니다.")
            elif token_count < 70:
                num_topics = min(3, num_topics)
                logger.warning(f"토큰 수({token_count})가 적어 토픽 수를 {num_topics}로 조정합니다.")
            else:
                # 100개 미만이지만 70개 이상이면 최소 4개 토픽
                num_topics = min(4, num_topics)
                logger.warning(f"토큰 수({token_count})가 충분하지 않아 토픽 수를 {num_topics}로 조정합니다.")
        elif orig_num_topics != 5:
            # 토큰이 충분하면 강제로 5개 토픽으로 설정
            num_topics = 5
            logger.info(f"토픽 수를 기본값 5로 설정합니다. (충분한 토큰: {token_count}개)")
        
        # 빈도수가 너무 적거나 많은 단어 필터링
        frequency = defaultdict(int)
        for token in tokens:
            frequency[token] += 1
            
        # 데이터 크기에 따라 필터링 기준 조정
        min_count = 1
        if token_count > 100:
            min_count = 2
            
        processed_tokens = [[token for token in tokens if frequency[token] >= min_count]]
        
        # 딕셔너리 및 코퍼스 생성
        dictionary = corpora.Dictionary(processed_tokens)
        
        # 최소 단어 수 확인
        if len(dictionary) < 5:  
            logger.warning(f"딕셔너리 크기가 너무 작습니다: {len(dictionary)}. 필터링 기준을 완화합니다.")
            # 필터링 기준 완화
            processed_tokens = [tokens]
            dictionary = corpora.Dictionary(processed_tokens)
            
        # 코퍼스 생성
        corpus = [dictionary.doc2bow(text) for text in processed_tokens]
        
        # 데이터가 충분한지 확인
        if not corpus or not corpus[0] or len(corpus[0]) < 3:
            logger.warning(f"코퍼스 데이터가 부족합니다: {len(corpus[0]) if corpus and corpus[0] else 0} 항목")
            # 데이터가 부족하면 토픽 수를 줄임
            num_topics = min(2, num_topics)
        
        # LDA 모델 생성
        lda_model = models.LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            passes=10,
            alpha='auto',
            iterations=50,
            random_state=42
        )
        
        # 토픽 추출
        topics = {}
        for i in range(num_topics):
            # 각 토픽의 주요 키워드 추출
            topic_keywords = lda_model.show_topic(i, topn=10)
            keywords = [word for word, prob in topic_keywords]
            weight = sum(prob for _, prob in topic_keywords)
            topics[i] = (keywords, weight)
        
        logger.info(f"LDA 모델 생성 완료: {num_topics}개 토픽 추출")
        return topics
        
    except Exception as e:
        logger.error(f"LDA 모델 생성 중 오류 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

def perform_lda(texts, language='en', num_topics=5):
    """
    Perform LDA topic modeling on the extracted content
    
    Args:
        texts (list): List of text content from URLs
        language (str): Language code ('en' or 'ko')
        num_topics (int): Number of topics to extract
    
    Returns:
        dict: Dictionary containing topics and visualization data
    """
    print(f"LDA 토픽 모델링 시작 - 텍스트 수: {len(texts)}, 언어: {language}, 토픽 수: {num_topics}")
    
    # 텍스트가 너무 적으면 경고
    if len(texts) < 3:
        print("경고: 텍스트가 매우 적습니다. 토픽 모델링 결과가 의미 없을 수 있습니다.")
    
    # Initialize modeler with appropriate language
    modeler = LDATopicModeler(language)
    
    # Preprocess texts
    processed_texts = modeler.preprocess_text(texts)
    
    # 처리된 텍스트가 없으면 오류 메시지 반환
    if not processed_texts:
        error_msg = "텍스트 처리 후 분석할 내용이 없습니다. 다른 검색어를 시도해보세요."
        print(error_msg)
        return {"error": error_msg}
    
    try:
        # Generate LDA model
        lda_model, corpus, dictionary = modeler.generate_lda_model(processed_texts, num_topics)
        
        # Generate visualization
        visualization = modeler.generate_visualization(lda_model, corpus, dictionary)
        
        # Format topics for display
        topics = modeler.format_topics(lda_model)
        
        print(f"LDA 토픽 모델링 완료 - {len(topics)}개 토픽 생성됨")
        
        return {
            "topics": topics,
            "visualization": visualization
        }
    except Exception as e:
        import traceback
        print(f"LDA 토픽 모델링 오류: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"토픽 모델링 오류: {str(e)}"}