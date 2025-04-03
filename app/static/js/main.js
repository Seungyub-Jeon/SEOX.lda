document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('search-query');
    const languageButtons = document.querySelectorAll('.language-switcher .btn');
    const loadingIndicator = document.getElementById('loading');
    const resultsContainer = document.getElementById('results-container');
    const errorContainer = document.getElementById('error-container') || document.createElement('div');
    const resultsCount = document.getElementById('results-count');
    const downloadBtn = document.getElementById('downloadBtn');
    const savedResultsBtn = document.getElementById('savedResultsBtn');
    const initSavedResultsBtn = document.getElementById('initSavedResultsBtn');
    
    // 로딩 표시/숨기기 함수
    function showLoadingIndicator() {
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
    }
    
    function hideLoadingIndicator() {
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
        }
    }
    
    // 모달 요소들
    const modalElements = {
        savedResultsModal: document.getElementById('savedResultsModal'),
        savedResultsList: document.getElementById('savedResultsList'),
        noSavedResults: document.getElementById('noSavedResults'),
        // 직접 표시 방식 요소 추가
        savedResultsSection: document.getElementById('savedResultsSection'),
        savedResultsListDirect: document.getElementById('savedResultsListDirect'),
        noSavedResultsDirect: document.getElementById('noSavedResultsDirect'),
        initSavedResultsBtn: document.getElementById('initSavedResultsBtn'),
        closeSavedResultsBtn: document.getElementById('closeSavedResultsBtn')
    };

    // 모달 요소 존재 여부 콘솔 출력
    console.log('모달 요소 체크:', {
        'savedResultsModal 존재': !!modalElements.savedResultsModal,
        'savedResultsList 존재': !!modalElements.savedResultsList,
        'noSavedResults 존재': !!modalElements.noSavedResults,
        'savedResultsSection 존재': !!modalElements.savedResultsSection,
        'savedResultsListDirect 존재': !!modalElements.savedResultsListDirect,
        'noSavedResultsDirect 존재': !!modalElements.noSavedResultsDirect
    });

    // Bootstrap 모달 초기화 또는 직접 표시 방식 설정
    let savedResultsModal;
    let useDirectDisplay = false;
    
    if (modalElements.savedResultsModal) {
        try {
            // Bootstrap 객체가 있는지 확인
            if (typeof bootstrap !== 'undefined') {
                savedResultsModal = new bootstrap.Modal(modalElements.savedResultsModal);
                console.log('모달이 성공적으로 초기화되었습니다.');
            } else {
                console.error('Bootstrap 객체가 정의되지 않았습니다. Bootstrap JS가 로드되었는지 확인하세요.');
                // jQuery가 있는 경우 대체 방법 시도
                if (typeof $ !== 'undefined') {
                    console.log('jQuery를 사용하여 모달 초기화를 시도합니다.');
                    savedResultsModal = {
                        show: function() { $(modalElements.savedResultsModal).modal('show'); },
                        hide: function() { $(modalElements.savedResultsModal).modal('hide'); }
                    };
                }
            }
        } catch (e) {
            console.error('모달 초기화 오류:', e);
            useDirectDisplay = true;
        }
    } else {
        console.log('모달 요소가 없으므로 직접 표시 방식을 사용합니다.');
        useDirectDisplay = true;
    }
    
    // 오류 컨테이너가 없으면 생성
    if (!document.getElementById('error-container')) {
        errorContainer.id = 'error-container';
        errorContainer.className = 'mt-3 hidden';
        document.querySelector('.row.mb-5').appendChild(errorContainer);
    }
    
    // 번역 객체
    const translations = {
        en: {
            errorTitle: "Error",
            apiErrorTitle: "API Error",
            apiErrorMessage: "There was an error with the API. Please check your API key in the config.py file.",
            noResultsTitle: "No Results",
            noResultsMessage: "No search results found. Please try a different query.",
            noContentTitle: "No Content",
            noContentMessage: "Could not extract content from search results. Please try a different query.",
            insufficientDataTitle: "Insufficient Data",
            insufficientDataMessage: "Not enough data for topic modeling. Please try a more general query.",
            tryAgainButton: "Try Again",
            unexpectedErrorTitle: "Unexpected Error",
            unexpectedErrorMessage: "An unexpected error occurred. Please try again later.",
            tokenCount: "Total tokens: ",
            topTokens: "Top Tokens:",
            downloadError: "Please perform a search first before trying to download results.",
            contentStructure: "Content Structure",
            seoRecommendations: "SEO Recommendations",
            primaryKeywords: "Primary Keywords",
            secondaryKeywords: "Secondary Keywords",
            relatedKeywords: "Related Keywords",
            networkErrorMessage: "A network error occurred. Please check your internet connection.",
            serverErrorMessage: "A server error occurred. Please try again later.",
            apiKeyErrorMessage: "API key is not properly set. Please check your config.py file.",
            savedResultsTitle: "Saved Analysis Results",
            loadResult: "Load",
            noSavedResults: "No saved analysis results found.",
            loadingResults: "Loading results..."
        },
        ko: {
            errorTitle: "오류",
            apiErrorTitle: "API 오류",
            apiErrorMessage: "API에 오류가 발생했습니다. config.py 파일에서 API 키를 확인하세요.",
            noResultsTitle: "결과 없음",
            noResultsMessage: "검색 결과가 없습니다. 다른 검색어를 시도하세요.",
            noContentTitle: "콘텐츠 없음",
            noContentMessage: "검색 결과에서 콘텐츠를 추출할 수 없습니다. 다른 검색어를 시도하세요.",
            insufficientDataTitle: "데이터 부족",
            insufficientDataMessage: "토픽 모델링을 위한 데이터가 충분하지 않습니다. 더 일반적인 검색어를 시도하세요.",
            tryAgainButton: "다시 시도",
            unexpectedErrorTitle: "예상치 못한 오류",
            unexpectedErrorMessage: "예상치 못한 오류가 발생했습니다. 나중에 다시 시도하세요.",
            tokenCount: "전체 토큰 수: ",
            topTokens: "상위 토큰:",
            downloadError: "결과를 다운로드하기 전에 먼저 검색을 수행하세요.",
            contentStructure: "콘텐츠 구조",
            seoRecommendations: "SEO 권장 사항",
            primaryKeywords: "주요 키워드",
            secondaryKeywords: "보조 키워드",
            relatedKeywords: "관련 키워드",
            networkErrorMessage: "네트워크 오류가 발생했습니다. 인터넷 연결을 확인하세요.",
            serverErrorMessage: "서버 오류가 발생했습니다. 나중에 다시 시도하세요.",
            apiKeyErrorMessage: "API 키가 올바르게 설정되지 않았습니다. config.py 파일을 확인하세요.",
            savedResultsTitle: "저장된 분석 결과",
            loadResult: "불러오기",
            noSavedResults: "저장된 분석 결과가 없습니다.",
            loadingResults: "결과 로딩 중..."
        }
    };

    // 현재 언어 설정 가져오기
    const getCurrentLanguage = () => {
        // URL에서 lang 파라미터 확인
        const urlParams = new URLSearchParams(window.location.search);
        const langParam = urlParams.get('lang');
        if (langParam && (langParam === 'ko' || langParam === 'en')) {
            return langParam;
        }
        
        // 언어 스위처에서 선택된 언어 가져오기
        const activeLang = document.querySelector('.language-switcher .btn-primary');
        if (activeLang) {
            return activeLang.textContent.includes('한국어') ? 'ko' : 'en';
        }
        
        // 기본값으로 한국어 반환
        return 'ko';
    };

    // 언어 전환 버튼 이벤트 리스너
    languageButtons.forEach(button => {
        button.addEventListener('click', function() {
            const language = this.textContent.includes('한국어') ? 'ko' : 'en';
            console.log('언어 변경:', language);
            
            // 모든 버튼에서 active 클래스 제거
            languageButtons.forEach(btn => {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-primary');
            });
            
            // 선택된 버튼에 active 클래스 추가
            this.classList.remove('btn-outline-primary');
            this.classList.add('btn-primary');
            
            // 언어별 요소 표시/숨김 처리
            document.querySelectorAll('.ko-text').forEach(el => {
                el.style.display = language === 'ko' ? '' : 'none';
            });
            
            document.querySelectorAll('.en-text').forEach(el => {
                el.style.display = language === 'en' ? '' : 'none';
            });
        });
    });
    
    // 초기 언어 설정 적용
    const initialLanguage = getCurrentLanguage();
    console.log('초기 언어:', initialLanguage);
    document.querySelectorAll('.ko-text').forEach(el => {
        el.style.display = initialLanguage === 'ko' ? '' : 'none';
    });
    
    document.querySelectorAll('.en-text').forEach(el => {
        el.style.display = initialLanguage === 'en' ? '' : 'none';
    });
    
    // languageButtons 업데이트
    const activeButton = initialLanguage === 'ko' 
        ? document.querySelector('.language-switcher .btn:first-child')
        : document.querySelector('.language-switcher .btn:last-child');
    
    if (activeButton) {
        languageButtons.forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-primary');
        });
        activeButton.classList.remove('btn-outline-primary');
        activeButton.classList.add('btn-primary');
    }

    // 오류 메시지 표시 함수
    function showErrorMessage(message, language) {
        // 기존 오류 메시지 제거
        errorContainer.innerHTML = '';
        
        const lang = language || getCurrentLanguage();
        const t = translations[lang];
        
        // 오류 유형 감지 및 메시지 생성
        let errorTitle = t.unexpectedErrorTitle;
        let errorMessage = message;
        
        if (message.includes("API 키") || message.includes("API key")) {
            errorTitle = t.apiErrorTitle;
        } else if (message.includes("검색 결과") || message.includes("search results")) {
            errorTitle = t.noResultsTitle;
        } else if (message.includes("내용을 추출") || message.includes("extract content")) {
            errorTitle = t.noContentTitle;
        } else if (message.includes("충분하지 않습니다") || message.includes("not enough")) {
            errorTitle = t.insufficientDataTitle;
        }
        
        // 오류 메시지 요소 생성
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message alert alert-danger';
        
        errorElement.innerHTML = `
            <h3>${errorTitle}</h3>
            <p>${errorMessage}</p>
            <button class="btn btn-outline-danger try-again-btn">${t.tryAgainButton}</button>
        `;
        
        // 오류 컨테이너에 추가
        errorContainer.appendChild(errorElement);
        errorContainer.classList.remove('d-none');
        
        // 다시 시도 버튼 이벤트 리스너
        const tryAgainBtn = errorElement.querySelector('.try-again-btn');
        tryAgainBtn.addEventListener('click', function() {
            errorContainer.classList.add('d-none');
            searchInput.focus();
        });
        
        // 결과 영역 숨기고 오류 표시
        resultsContainer.classList.add('d-none');
        loadingIndicator.classList.add('d-none');
    }

    // 검색 수행 함수
    function performSearch(query, language) {
        // 화면 초기화
        if (errorContainer) errorContainer.classList.add('d-none');
        resultsContainer.classList.add('d-none');
        loadingIndicator.classList.remove('d-none');
        
        console.log(`검색 실행: ${query}, 언어: ${language}`);
        
        // 서버에 검색 요청
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                language: language
            })
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('d-none');
            
            // 오류 확인
            if (data.error) {
                showErrorMessage(data.error, language);
                return;
            }
            
            // 결과 표시
            displayResults(data, language);
        })
        .catch(error => {
            loadingIndicator.classList.add('d-none');
            showErrorMessage(`${translations[language].unexpectedErrorMessage}: ${error.message}`, language);
        });
    }

    // 언어와 결과 데이터에 따라 결과 표시
    function displayResults(data, language) {
        console.log('결과 표시:', data);
        
        // 결과 컨테이너 표시 및 로딩 인디케이터 숨기기
        hideLoadingIndicator();
        resultsContainer.classList.remove('d-none');
        
        // 다운로드 버튼 URL 설정
        if (downloadBtn) {
            downloadBtn.href = `/download_lda_results?timestamp=${data.timestamp}`;
        }
        
        // 요약 정보 표시
        displayResultsSummary(data, language);
        
        // 토큰 통계 표시
        displayTokenStats(data, language);
        
        // 토픽 요약 표시
        displayTopicsSummary(data.topics);
        
        // 토픽 시각화 표시
        displayTopicVisualization(data);
        
        // 참고 콘텐츠 URL 및 토픽 분포 표시
        displayReferenceURLs(data);
        
        // 주요 토픽 상세 정보 표시
        displayTopicsDetails(data);
        
        // 결과 데이터 저장 (로컬 스토리지)
        addToSavedResults(data);
    }

    // 토큰 통계 표시 함수
    function displayTokenStats(data, language) {
        const tokenCount = document.getElementById('token-count');
        const topTokens = document.getElementById('top-tokens');
        
        if (tokenCount) {
            const language = document.documentElement.lang || 'ko';
            // token_analysis 객체에서 total_tokens 사용
            tokenCount.textContent = language === 'ko' 
                ? `총 토큰 수: ${data.token_analysis?.total_tokens || 0}` 
                : `Total tokens: ${data.token_analysis?.total_tokens || 0}`;
        }
        
        if (topTokens) {
            topTokens.innerHTML = ''; // 기존 내용 지우기
            
            // token_analysis 객체에서 top_tokens 사용
            if (data.token_analysis?.top_tokens && data.token_analysis.top_tokens.length > 0) {
                // 최대 빈도수 계산
                const maxFreq = data.token_analysis.top_tokens[0][1];
                const minFreq = data.token_analysis.top_tokens[data.token_analysis.top_tokens.length - 1][1];
                const freqRange = maxFreq - minFreq;
                
                data.token_analysis.top_tokens.forEach(token => {
                    const [word, freq] = token;
                    const tokenEl = document.createElement('span');
                    tokenEl.className = 'token-badge';
                    
                    // 토큰 빈도에 따른 클래스 추가
                    if (freq >= maxFreq * 0.7) {
                        tokenEl.classList.add('high-freq');
                    } else if (freq >= maxFreq * 0.4) {
                        tokenEl.classList.add('medium-freq');
                    } else {
                        tokenEl.classList.add('low-freq');
                    }
                    
                    tokenEl.innerHTML = `${word} <span class="frequency">(${freq})</span>`;
                    topTokens.appendChild(tokenEl);
                });
            } else {
                topTokens.textContent = document.documentElement.lang === 'ko' 
                    ? '토큰 정보가 없습니다.' 
                    : 'No token information available.';
            }
        }
    }

    // 토픽 요약 정보 표시 함수 (새로 추가)
    function displayTopicsSummary(topics) {
        const topicsSummaryContainer = document.getElementById('topics-summary-container');
        if (!topicsSummaryContainer) return;
        
        topicsSummaryContainer.innerHTML = ''; // 기존 내용 지우기
        
        console.log('토픽 요약 표시 시작', topics);
        
        // 최대 5개 토픽에 대해 요약 카드 생성
        const topicsToShow = Math.min(topics.length, 5);
        
        for (let i = 0; i < topicsToShow; i++) {
            const topic = topics[i];
            const topicCard = document.createElement('div');
            topicCard.className = 'col-md-4 col-sm-6 mb-3';
            
            // 배경색 목록 (부드러운 색상)
            const bgColors = ['#e8f4f8', '#e8f4e5', '#f8f2e8', '#f5e8f8', '#f8e8e8'];
            
            // 키워드 형식 확인
            console.log(`토픽 ${i+1} 키워드:`, topic.keywords.slice(0, 2));
            
            // 토픽 키워드 가져오기 (상위 5개만)
            const topKeywords = topic.keywords.slice(0, 5).map(k => 
                typeof k === 'string' ? k : (Array.isArray(k) ? k[0] : k)
            ).join(', ');
            
            // 안전하게 가중치 표시
            const weightDisplay = typeof topic.weight === 'number' ? 
                (topic.weight * 100).toFixed(1) : 
                (parseFloat(topic.weight) * 100).toFixed(1) || '0.0';
            
            topicCard.innerHTML = `
                <div class="topic-summary-card" style="border-top: 3px solid ${getTopicColor(i)}">
                    <div class="card-header">
                        토픽 ${i + 1} <span class="float-end badge rounded-pill bg-secondary">${weightDisplay}%</span>
                    </div>
                    <div class="card-body">
                        <div class="topic-keywords-summary">
                            ${topic.keywords.slice(0, 5).map(kw => {
                                // 키워드와 가중치 안전하게 추출
                                let keyword, weight;
                                if (Array.isArray(kw)) {
                                    keyword = kw[0];
                                    weight = kw[1];
                                } else if (typeof kw === 'object') {
                                    keyword = kw.word || kw.term || '';
                                    weight = kw.weight || kw.value || 0;
                                } else {
                                    keyword = kw;
                                    weight = '';
                                }
                                
                                // 가중치 표시 형식 결정
                                const weightText = typeof weight === 'number' ? 
                                    weight.toFixed(3) : 
                                    (typeof weight === 'string' ? weight : '');
                                
                                return `<span class="badge" style="background-color: ${getTopicColor(i, 0.2)}; color: ${getTopicColor(i, 1.0)};">
                                    ${keyword} ${weightText ? `<small>${weightText}</small>` : ''}
                                </span>`;
                            }).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            topicsSummaryContainer.appendChild(topicCard);
        }
    }
    
    // 토픽 색상 생성 함수
    function getTopicColor(index, opacity = 1.0) {
        const colors = [
            `rgba(52, 152, 219, ${opacity})`,  // 파란색
            `rgba(46, 204, 113, ${opacity})`,  // 녹색
            `rgba(230, 126, 34, ${opacity})`,  // 주황색
            `rgba(155, 89, 182, ${opacity})`,  // 보라색
            `rgba(231, 76, 60, ${opacity})`,   // 빨간색
            `rgba(241, 196, 15, ${opacity})`,  // 노란색
            `rgba(26, 188, 156, ${opacity})`,  // 청록색
            `rgba(243, 156, 18, ${opacity})`,  // 황갈색
            `rgba(142, 68, 173, ${opacity})`,  // 자주색
            `rgba(192, 57, 43, ${opacity})`    // 암적색
        ];
        
        return colors[index % colors.length];
    }

    // 토픽 시각화 함수
    function displayTopicVisualization(data) {
        const topicChart = document.getElementById('topic-chart');
        if (!topicChart) return;
        
        console.log('토픽 시각화 시작:', data);
        
        // 간단한 토픽 시각화 생성 (막대 그래프)
        const topics = data.topics;
        if (!topics || topics.length === 0) return;
        
        // 토픽 가중치 데이터 준비
        const labels = topics.map((_, i) => `토픽 ${i + 1}`);
        const values = topics.map(topic => {
            // 안전하게 가중치 값 추출
            return typeof topic.weight === 'number' ? 
                topic.weight : 
                parseFloat(topic.weight) || 0;
        });
        const colors = topics.map((_, i) => getTopicColor(i, 0.7));
        
        // Plotly.js 사용하여 막대 그래프 생성
        const plotData = [{
            x: labels,
            y: values,
            type: 'bar',
            marker: {
                color: colors
            },
            text: values.map(v => (v * 100).toFixed(1) + '%'),
            textposition: 'auto',
            hoverinfo: 'text',
            hovertext: topics.map((topic, i) => {
                // 안전하게 키워드 추출
                let keywordText = '';
                try {
                    const keywords = topic.keywords.slice(0, 5).map(k => {
                        if (Array.isArray(k)) return k[0];
                        if (typeof k === 'object') return k.word || k.term || '';
                        return k;
                    }).join(', ');
                    
                    const weightText = (typeof topic.weight === 'number' ? 
                        (topic.weight * 100).toFixed(1) : 
                        (parseFloat(topic.weight) * 100).toFixed(1) || '0.0');
                    
                    keywordText = `토픽 ${i + 1}<br>가중치: ${weightText}%<br>주요 키워드: ${keywords}`;
                } catch (e) {
                    console.error('키워드 추출 오류:', e);
                    keywordText = `토픽 ${i + 1}`;
                }
                return keywordText;
            })
        }];
        
        const layout = {
            title: '토픽 분포',
            xaxis: {
                title: '토픽'
            },
            yaxis: {
                title: '가중치',
                range: [0, Math.max(...values) * 1.2]
            },
            margin: {
                l: 50,
                r: 50,
                b: 50,
                t: 50,
                pad: 4
            }
        };
        
        // 그래프 생성
        try {
            Plotly.newPlot('topic-chart', plotData, layout);
        } catch (e) {
            console.error('그래프 생성 오류:', e);
            topicChart.innerHTML = '<p class="text-danger">토픽 차트를 생성할 수 없습니다.</p>';
        }
        
        // 시각화 컨테이너에 추가 정보 표시
        const visualizationContainer = document.getElementById('visualization-container');
        if (visualizationContainer) {
            try {
                // 주요 토픽 간의 관계 설명
                visualizationContainer.innerHTML = `
                    <div class="mt-4 p-3 bg-light rounded">
                        <h5>토픽 간 관계</h5>
                        <p>주요 토픽에서 반복되는 키워드를 분석하면 콘텐츠의 핵심 주제를 파악할 수 있습니다.</p>
                        <div class="common-keywords mt-3">
                            <h6>공통 키워드</h6>
                            <div id="common-keywords" class="d-flex flex-wrap gap-2 mt-2">
                                ${findCommonKeywords(topics)}
                            </div>
                        </div>
                    </div>
                `;
            } catch (e) {
                console.error('시각화 컨테이너 업데이트 오류:', e);
                visualizationContainer.innerHTML = '<p class="text-danger">토픽 관계 정보를 표시할 수 없습니다.</p>';
            }
        }
    }
    
    // 공통 키워드 찾기 함수
    function findCommonKeywords(topics) {
        try {
            // 모든 키워드를 추출하여 빈도 계산
            const keywordFrequency = {};
            const topicCount = topics.length;
            
            topics.forEach(topic => {
                if (!Array.isArray(topic.keywords)) {
                    console.log('키워드가 배열이 아님:', topic);
                    return;
                }
                
                // 각 토픽의 상위 10개 키워드만 고려
                const topKeywords = topic.keywords.slice(0, 10).map(k => {
                    if (Array.isArray(k)) return k[0];
                    if (typeof k === 'object') return k.word || k.term || '';
                    return k;
                });
                
                topKeywords.forEach(keyword => {
                    if (!keyword) return; // 빈 키워드 건너뛰기
                    
                    if (!keywordFrequency[keyword]) {
                        keywordFrequency[keyword] = 1;
                    } else {
                        keywordFrequency[keyword]++;
                    }
                });
            });
            
            // 두 개 이상의 토픽에서 등장하는 키워드 필터링
            const commonKeywords = Object.entries(keywordFrequency)
                .filter(([_, count]) => count >= 2)
                .sort((a, b) => b[1] - a[1]) // 빈도 내림차순 정렬
                .slice(0, 10); // 상위 10개만 표시
            
            if (commonKeywords.length === 0) {
                return '<span class="text-muted">공통 키워드가 없습니다.</span>';
            }
            
            // 공통 키워드 HTML 생성
            return commonKeywords.map(([keyword, count]) => {
                const opacity = 0.3 + (count / topicCount) * 0.7; // 빈도에 따른 불투명도 조정
                return `<span class="badge bg-secondary" style="opacity: ${opacity};">${keyword} (${count}/${topicCount})</span>`;
            }).join('');
        } catch (e) {
            console.error('공통 키워드 찾기 오류:', e);
            return '<span class="text-danger">키워드 분석 중 오류가 발생했습니다.</span>';
        }
    }

    // 키워드 분포 표시 함수
    function displayKeywordDistribution(data) {
        const keywordDistribution = document.getElementById('keyword-distribution');
        if (!keywordDistribution) return;
        
        if (!data.top_tokens || data.top_tokens.length === 0) {
            keywordDistribution.innerHTML = '<p class="text-muted">키워드 정보가 없습니다.</p>';
            return;
        }
        
        // 상위 토큰을 기반으로 키워드 분류
        const topTokens = data.top_tokens;
        const topCount = Math.min(5, topTokens.length);
        const secondaryCount = Math.min(10, topTokens.length) - topCount;
        const relatedCount = Math.min(15, topTokens.length) - topCount - secondaryCount;
        
        // 주요/보조/관련 키워드 분류
        const primaryKeywords = topTokens.slice(0, topCount);
        const secondaryKeywords = topTokens.slice(topCount, topCount + secondaryCount);
        const relatedKeywords = topTokens.slice(topCount + secondaryCount, topCount + secondaryCount + relatedCount);
        
        // HTML 생성
        keywordDistribution.innerHTML = `
            <div class="keyword-category mb-3">
                <h6 class="keyword-category-title">주요 키워드</h6>
                <div class="keyword-badges">
                    ${primaryKeywords.map(token => 
                        `<span class="keyword-tag primary-keyword">${token[0]} <span class="keyword-frequency">(${token[1]})</span></span>`
                    ).join('')}
                </div>
            </div>
            <div class="keyword-category mb-3">
                <h6 class="keyword-category-title">보조 키워드</h6>
                <div class="keyword-badges">
                    ${secondaryKeywords.map(token => 
                        `<span class="keyword-tag secondary-keyword">${token[0]} <span class="keyword-frequency">(${token[1]})</span></span>`
                    ).join('')}
                </div>
            </div>
            <div class="keyword-category mb-3">
                <h6 class="keyword-category-title">관련 키워드</h6>
                <div class="keyword-badges">
                    ${relatedKeywords.map(token => 
                        `<span class="keyword-tag related-keyword">${token[0]} <span class="keyword-frequency">(${token[1]})</span></span>`
                    ).join('')}
                </div>
            </div>
        `;
    }

    // 주요 토픽 상세 정보 표시 함수
    function displayTopicsDetails(data) {
        const topicsContainer = document.getElementById('topics-container');
        if (!topicsContainer) return;
        
        topicsContainer.innerHTML = ''; // 기존 내용 지우기
        console.log('토픽 상세 정보 표시:', data.topics);
        
        // 토픽 데이터 확인
        if (!data.topics || !Array.isArray(data.topics) || data.topics.length === 0) {
            topicsContainer.innerHTML = '<p class="text-muted">토픽 정보가 없습니다.</p>';
            return;
        }
        
        // 토픽 상세 정보 표시
        displayTopics(data.topics);
    }

    // 결과 요약 표시 함수
    function displayResultsSummary(data, language) {
        // 검색어와 결과 수 표시
        const searchResultsTitle = document.getElementById('search-results-title');
        if (searchResultsTitle) {
            searchResultsTitle.textContent = language === 'ko' 
                ? `"${data.query}" 검색 결과` 
                : `Search results for "${data.query}"`;
        }
        
        // 검색 결과 URL 목록 표시
        const searchResultsList = document.getElementById('search-results-list');
        if (searchResultsList) {
            searchResultsList.innerHTML = ''; // 기존 내용 지우기
            
            if (data.search_results && data.search_results.length > 0) {
                data.search_results.forEach(result => {
                    const listItem = document.createElement('li');
                    listItem.className = 'search-result-item';
                    
                    // URL 표시
                    listItem.innerHTML = `
                        <div class="search-result-url">
                            <a href="${result.url}" target="_blank" rel="noopener noreferrer">${result.url}</a>
                        </div>
                        <div class="search-result-title">${result.title || '제목 없음'}</div>
                        <div class="search-result-snippet">${result.snippet || '내용 없음'}</div>
                    `;
                    
                    searchResultsList.appendChild(listItem);
                });
            } else {
                // 검색 결과가 없는 경우 메시지 표시
                const noResultsMsg = document.createElement('li');
                noResultsMsg.className = 'no-results-message';
                noResultsMsg.textContent = language === 'ko' 
                    ? '검색 결과가 없습니다.' 
                    : 'No search results found.';
                searchResultsList.appendChild(noResultsMsg);
            }
        }
        
        // 키워드 분포 표시
        displayKeywordDistribution(data);
    }

    // 현재 결과를 저장된 결과에 추가
    function addToSavedResults(data) {
        // 서버에서 자동 저장되므로 클라이언트에서는 별도 작업 필요 없음
        console.log('분석 결과 자동 저장됨');
    }

    // 토픽 상세 정보 표시 함수
    function displayTopics(topics) {
        const topicsContainer = document.getElementById('topics-container');
        if (!topicsContainer) return;
        
        topicsContainer.innerHTML = ''; // 기존 내용 지우기
        console.log('토픽 상세 정보 표시:', topics);
        
        topics.forEach((topic, index) => {
            const topicDiv = document.createElement('div');
            topicDiv.className = 'topic-item';
            
            // 토픽 헤더 (토픽 번호와 가중치)
            const topicHeader = document.createElement('div');
            topicHeader.className = 'topic-header';
            
            const topicIdSpan = document.createElement('span');
            topicIdSpan.className = 'topic-id';
            topicIdSpan.textContent = `토픽 ${index + 1}`;
            
            // 안전하게 가중치 표시
            const weightDisplay = typeof topic.weight === 'number' ? 
                (topic.weight * 100).toFixed(1) : 
                (parseFloat(topic.weight) * 100).toFixed(1) || '0.0';
            
            const topicWeightSpan = document.createElement('span');
            topicWeightSpan.className = 'topic-weight';
            topicWeightSpan.textContent = `${weightDisplay}%`;
            
            topicHeader.appendChild(topicIdSpan);
            topicHeader.appendChild(topicWeightSpan);
            topicDiv.appendChild(topicHeader);
            
            // 토픽 키워드 표시
            const topicKeywords = document.createElement('div');
            topicKeywords.className = 'topic-keywords';
            
            // 키워드 배지 생성
            if (Array.isArray(topic.keywords)) {
                topic.keywords.forEach((kw, kIndex) => {
                    // 키워드와 가중치 안전하게 추출
                    let keyword, weight;
                    if (Array.isArray(kw)) {
                        keyword = kw[0];
                        weight = kw[1];
                    } else if (typeof kw === 'object') {
                        keyword = kw.word || kw.term || '';
                        weight = kw.weight || kw.value || 0;
                    } else {
                        keyword = kw;
                        weight = '';
                    }
                    
                    const keywordSpan = document.createElement('span');
                    keywordSpan.className = 'keyword-tag';
                    
                    // 상위 5개 키워드는 주요 키워드로 표시
                    if (kIndex < 5) {
                        keywordSpan.classList.add('primary-keyword');
                    } else if (kIndex < 10) {
                        keywordSpan.classList.add('secondary-keyword');
                    } else {
                        keywordSpan.classList.add('related-keyword');
                    }
                    
                    // 가중치 표시 형식 결정
                    const weightText = typeof weight === 'number' ? 
                        weight.toFixed(3) : 
                        (typeof weight === 'string' ? weight : '');
                    
                    keywordSpan.innerHTML = `${keyword} ${weightText ? `<span class="keyword-frequency">(${weightText})</span>` : ''}`;
                    topicKeywords.appendChild(keywordSpan);
                });
            } else {
                // 키워드가 배열이 아닌 경우 (예: 문자열 또는 다른 형식)
                const keywordSpan = document.createElement('span');
                keywordSpan.className = 'keyword-tag';
                keywordSpan.textContent = '키워드 정보가 없거나 잘못된 형식입니다.';
                topicKeywords.appendChild(keywordSpan);
            }
            
            topicDiv.appendChild(topicKeywords);
            topicsContainer.appendChild(topicDiv);
        });
    }
    
    // 다운로드 버튼 클릭 이벤트 리스너
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            const language = getCurrentLanguage();
            window.location.href = '/download_lda_results';
        });
    }

    // 검색 버튼 클릭 이벤트 리스너
    searchButton.addEventListener('click', function() {
        const query = searchInput.value.trim();
        const language = getCurrentLanguage();
        
        if (!query) {
            return;
        }
        
        performSearch(query, language);
    });
    
    // 검색 입력란에서 엔터 키 이벤트 리스너
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            const language = getCurrentLanguage();
            
            if (!query) {
                return;
            }
            
            performSearch(query, language);
        }
    });

    // 저장된 결과 버튼 이벤트 핸들러 설정
    if (savedResultsBtn) {
        savedResultsBtn.addEventListener('click', function() {
            if (useDirectDisplay) {
                loadSavedResultsDirect();
            } else {
                loadSavedResults();
            }
        });
    }
    
    // 초기 화면의 저장된 결과 버튼 이벤트 핸들러
    if (initSavedResultsBtn) {
        initSavedResultsBtn.addEventListener('click', function() {
            if (useDirectDisplay) {
                loadSavedResultsDirect();
            } else {
                loadSavedResults();
            }
        });
    }
    
    // 닫기 버튼 이벤트 핸들러 설정
    if (modalElements.closeSavedResultsBtn) {
        modalElements.closeSavedResultsBtn.addEventListener('click', function() {
            if (modalElements.savedResultsSection) {
                modalElements.savedResultsSection.classList.add('d-none');
            }
        });
    }
    
    // 저장된 결과 로드 함수 - 모달 사용 방식
    function loadSavedResults() {
        console.log('저장된 결과 로드 - 모달 방식');
        
        // 모달 요소가 없으면 직접 표시 방식으로 전환
        if (!modalElements.savedResultsModal || !modalElements.savedResultsList || !modalElements.noSavedResults) {
            console.warn('모달 요소가 없어 직접 표시 방식으로 전환합니다.');
            loadSavedResultsDirect();
            return;
        }
        
        // 저장된 결과 목록 가져오기
        fetch('/list_saved_results')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showErrorMessage(data.error);
                    return;
                }
                
                // 결과 목록 업데이트
                const results = data.results || [];
                if (results.length === 0) {
                    modalElements.savedResultsList.innerHTML = '';
                    modalElements.noSavedResults.classList.remove('d-none');
                } else {
                    modalElements.noSavedResults.classList.add('d-none');
                    
                    // 결과 목록 표시
                    modalElements.savedResultsList.innerHTML = '';
                    results.forEach(result => {
                        const date = formatTimestamp(result.timestamp);
                        
                        const row = document.createElement('tr');
                        const lang = getCurrentLanguage();
                        const loadButtonText = lang === 'ko' ? '불러오기' : 'Load';
                        
                        row.innerHTML = `
                            <td>${result.query}</td>
                            <td>${date}</td>
                            <td>${result.num_topics || 0}</td>
                            <td>${result.token_count || 0}</td>
                            <td>
                                <button class="btn btn-sm btn-primary load-result-btn" 
                                        data-filename="${result.filename}">${loadButtonText}</button>
                            </td>
                        `;
                        modalElements.savedResultsList.appendChild(row);
                    });
                    
                    // 결과 로드 버튼 이벤트 리스너 추가
                    document.querySelectorAll('.load-result-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const filename = this.getAttribute('data-filename');
                            savedResultsModal.hide();
                            loadSavedResult(filename);
                        });
                    });
                }
                
                // 모달 표시
                savedResultsModal.show();
            })
            .catch(error => {
                console.error('저장된 결과 로드 중 오류:', error);
                const lang = getCurrentLanguage();
                showErrorMessage(translations[lang].serverErrorMessage);
            });
    }
    
    // 저장된 결과 목록 직접 페이지에 표시
    function loadSavedResultsDirect() {
        console.log('저장된 결과 로드 시작 (직접 표시 방식)');
        
        if (!modalElements.savedResultsSection || !modalElements.savedResultsListDirect || !modalElements.noSavedResultsDirect) {
            console.error('저장된 결과 섹션 요소를 찾을 수 없습니다.', {
                savedResultsSection: !!modalElements.savedResultsSection,
                savedResultsList: !!modalElements.savedResultsListDirect,
                noSavedResults: !!modalElements.noSavedResultsDirect
            });
            alert('저장된 결과를 표시할 수 없습니다. 페이지를 새로고침하세요.');
            return;
        }
        
        // 로딩 상태 표시
        const lang = getCurrentLanguage();
        const t = translations[lang];
        modalElements.savedResultsListDirect.innerHTML = `<tr><td colspan="5" class="text-center">${t.loadingResults || '로딩 중...'}</td></tr>`;
        
        // 섹션 표시 - 클래스를 직접 조작
        console.log('결과 섹션 표시 시도 - 이전 상태:', modalElements.savedResultsSection.className);
        modalElements.savedResultsSection.style.display = 'block';
        modalElements.savedResultsSection.classList.remove('d-none');
        console.log('결과 섹션 표시 후 상태:', modalElements.savedResultsSection.className);
        
        // 결과 영역으로 스크롤 이동
        setTimeout(() => {
            modalElements.savedResultsSection.scrollIntoView({behavior: 'smooth'});
            console.log('결과 섹션으로 스크롤 이동');
        }, 300);
        
        // 저장된 결과 목록 가져오기
        fetch('/list_saved_results')
            .then(response => {
                console.log('응답 상태:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('응답 데이터:', data);
                
                if (data.error) {
                    showErrorMessage(data.error);
                    return;
                }
                
                const results = data.results || [];
                console.log('결과 개수:', results.length);
                
                if (results.length === 0) {
                    modalElements.savedResultsListDirect.innerHTML = '';
                    modalElements.noSavedResultsDirect.classList.remove('d-none');
                    console.log('저장된 결과가 없습니다.');
                } else {
                    modalElements.noSavedResultsDirect.classList.add('d-none');
                    
                    // 결과 목록 표시
                    modalElements.savedResultsListDirect.innerHTML = '';
                    results.forEach((result, index) => {
                        console.log(`결과 #${index + 1}:`, result);
                        const date = formatTimestamp(result.timestamp);
                        console.log(`포맷팅된 날짜: ${date}`);
                        
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${result.query}</td>
                            <td>${date}</td>
                            <td>${result.num_topics || 0}</td>
                            <td>${result.token_count || 0}</td>
                            <td>
                                <button class="btn btn-sm btn-primary load-result-btn" 
                                        data-filename="${result.filename}">${t.loadResult || '불러오기'}</button>
                            </td>
                        `;
                        modalElements.savedResultsListDirect.appendChild(row);
                    });
                    
                    // 결과 로드 버튼 이벤트 리스너 추가
                    document.querySelectorAll('.load-result-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const filename = this.getAttribute('data-filename');
                            console.log('불러오기 버튼 클릭:', filename);
                            
                            // 결과 섹션 숨기기
                            modalElements.savedResultsSection.classList.add('d-none');
                            
                            // 선택된 결과 불러오기
                            loadSavedResult(filename);
                        });
                    });
                }
                
                // 결과 영역이 제대로 표시되었는지 다시 확인
                console.log('결과 섹션 상태 확인:', {
                    display: modalElements.savedResultsSection.style.display,
                    className: modalElements.savedResultsSection.className,
                    isVisible: !modalElements.savedResultsSection.classList.contains('d-none'),
                    offsetHeight: modalElements.savedResultsSection.offsetHeight,
                    clientHeight: modalElements.savedResultsSection.clientHeight
                });
            })
            .catch(error => {
                console.error('저장된 결과 로드 중 오류:', error);
                modalElements.savedResultsListDirect.innerHTML = `<tr><td colspan="5" class="text-center text-danger">결과 로드 중 오류가 발생했습니다: ${error.message}</td></tr>`;
            });
    }
    
    // 저장된 특정 결과 불러오기
    function loadSavedResult(filename) {
        if (!filename) {
            console.error('불러올 파일 이름이 지정되지 않았습니다.');
            return;
        }
        
        console.log('저장된 결과 불러오기:', filename);
        showLoadingIndicator();
        
        fetch(`/load_saved_result/${filename}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`서버 응답 오류: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('불러온 데이터:', data);
                hideLoadingIndicator();
                
                if (data.error) {
                    showErrorMessage(data.error);
                    return;
                }
                
                // 검색 쿼리 입력란에 설정
                if (searchInput && data.query) {
                    searchInput.value = data.query;
                }
                
                // 결과 표시
                displayResults(data, getCurrentLanguage());
            })
            .catch(error => {
                hideLoadingIndicator();
                console.error('저장된 결과 불러오기 중 오류:', error);
                const t = translations[getCurrentLanguage()];
                showErrorMessage(t.serverErrorMessage);
            });
    }
    
    // 타임스탬프 포맷팅 (YYYYMMDD_HHMMSS -> YYYY-MM-DD HH:MM:SS)
    function formatTimestamp(timestamp) {
        console.log('포맷팅할 타임스탬프:', timestamp);
        
        if (!timestamp) return '-';
        
        // 타임스탬프 형식이 YYYYMMDD_HHMMSS인지 확인
        if (typeof timestamp === 'string' && timestamp.length >= 15 && timestamp.indexOf('_') > 0) {
            try {
                const parts = timestamp.split('_');
                if (parts.length < 2) return timestamp;
                
                const datePart = parts[0];
                const timePart = parts[1].substring(0, 6); // HHMMSS 부분만
                
                const year = datePart.substring(0, 4);
                const month = datePart.substring(4, 6);
                const day = datePart.substring(6, 8);
                
                const hour = timePart.substring(0, 2);
                const minute = timePart.substring(2, 4);
                const second = timePart.length >= 6 ? timePart.substring(4, 6) : '00';
                
                return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
            } catch (e) {
                console.error('타임스탬프 포맷팅 오류:', e);
                return timestamp;
            }
        }
        
        return timestamp;
    }

    // 참고 콘텐츠 URL 및 토픽 분포 표시 함수
    function displayReferenceURLs(data) {
        const container = document.getElementById('reference-urls-container');
        const urlsList = document.getElementById('reference-urls-list');
        const noUrls = document.getElementById('no-reference-urls');
        
        if (!container || !urlsList || !noUrls) {
            console.error('참고 콘텐츠 URL 표시 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 기존 내용 초기화
        urlsList.innerHTML = '';
        
        // URL 토픽 분포 데이터 확인
        const urlData = data.url_topic_distribution;
        
        if (!urlData || urlData.length === 0) {
            // URL 데이터가 없는 경우
            noUrls.classList.remove('d-none');
            return;
        }
        
        // URL 데이터가 있는 경우 메시지 숨기기
        noUrls.classList.add('d-none');
        
        // 토픽 색상 정보 가져오기 (기존 함수 재사용)
        const getTopicColorForBar = function(topicId) {
            const colorScheme = [
                'rgba(54, 162, 235, 0.8)',   // Blue
                'rgba(255, 99, 132, 0.8)',   // Red
                'rgba(75, 192, 192, 0.8)',   // Green
                'rgba(255, 159, 64, 0.8)',   // Orange
                'rgba(153, 102, 255, 0.8)'   // Purple
            ];
            return colorScheme[topicId % colorScheme.length];
        };
        
        // 각 URL에 대한 정보 추가
        urlData.forEach(item => {
            const row = document.createElement('tr');
            
            // 제목 준비
            const title = item.title || '제목 없음';
            
            // URL 준비
            const url = item.url;
            const truncatedUrl = url.length > 40 ? url.substring(0, 40) + '...' : url;
            
            // 주요 토픽 찾기 (가장 높은 비중의 토픽)
            let mainTopic = { topic_id: -1, weight: 0 };
            
            if (item.topic_distribution && item.topic_distribution.length > 0) {
                mainTopic = item.topic_distribution.reduce((prev, current) => 
                    (current.weight > prev.weight) ? current : prev, { topic_id: -1, weight: 0 });
            }
            
            // 주요 토픽의 키워드 가져오기
            let mainTopicKeywords = '';
            if (mainTopic.topic_id >= 0 && data.topics && data.topics.length > mainTopic.topic_id) {
                // 해당 토픽의 키워드 상위 3개 추출
                const topicInfo = data.topics[mainTopic.topic_id];
                if (topicInfo && topicInfo.keywords) {
                    mainTopicKeywords = topicInfo.keywords.slice(0, 3).join(', ');
                }
            }
            
            // 토픽 분포 바 차트 만들기
            let topicDistributionHtml = '<div class="topic-distribution-bar" style="width:100%; height:20px; display:flex;">';
            
            if (item.topic_distribution && item.topic_distribution.length > 0) {
                // 토픽별 분포 정렬
                const sortedDist = [...item.topic_distribution].sort((a, b) => b.weight - a.weight);
                
                // 토픽 분포 바 생성
                sortedDist.forEach(topic => {
                    const width = Math.max(5, Math.round(topic.weight * 100)); // 최소 5% 너비 보장
                    const color = getTopicColorForBar(topic.topic_id);
                    topicDistributionHtml += `
                        <div class="topic-bar" 
                            data-topic-id="${topic.topic_id}"
                            data-weight="${topic.weight.toFixed(2)}"
                            style="width:${width}%; height:100%; background-color:${color}; position:relative;">
                            <span class="topic-tooltip" style="display:none; position:absolute; bottom:25px; left:0; 
                                background-color:rgba(0,0,0,0.8); color:white; padding:5px; border-radius:3px; font-size:12px;">
                                토픽 ${topic.topic_id + 1}: ${(topic.weight * 100).toFixed(1)}%
                            </span>
                        </div>
                    `;
                });
            } else {
                topicDistributionHtml += '<div class="topic-bar" style="width:100%; height:100%; background-color:#ccc;"></div>';
            }
            
            topicDistributionHtml += '</div>';
            
            // 행 구성
            row.innerHTML = `
                <td>${title}</td>
                <td><a href="${url}" target="_blank" title="${url}">${truncatedUrl}</a></td>
                <td>${mainTopic.topic_id >= 0 ? '토픽 ' + (mainTopic.topic_id + 1) + ': ' + mainTopicKeywords : '분석 불가'}</td>
                <td>${topicDistributionHtml}</td>
            `;
            
            // 토픽 바에 호버 이벤트 추가 (DOM에 추가 후)
            setTimeout(() => {
                const topicBars = row.querySelectorAll('.topic-bar');
                topicBars.forEach(bar => {
                    bar.addEventListener('mouseenter', function() {
                        this.querySelector('.topic-tooltip').style.display = 'block';
                    });
                    bar.addEventListener('mouseleave', function() {
                        this.querySelector('.topic-tooltip').style.display = 'none';
                    });
                });
            }, 100);
            
            // 테이블에 행 추가
            urlsList.appendChild(row);
        });
    }
});