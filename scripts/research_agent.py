import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# 1. API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCIENCEON_API_KEY = os.getenv("SCIENCEON_API_KEY")

# 2. Gemini 모델 설정 (2.5 Flash)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_mock_papers():
    """API 승인 대기 기간 동안 사용할 가상의 논문 데이터를 생성합니다."""
    prompt = """
    너는 ScienceON API 역할을 수행해. 
    'Smart City', 'GIS', '교통 데이터', '데이터 사이언스'와 관련된 
    최신 국내 가상 논문 5개의 정보를 JSON 형식으로 만들어줘.
    형식: [{"title": "...", "author": "...", "abstract": "...", "link": "..."}]
    """
    try:
        # JSON 출력을 유도하기 위해 response_mime_type 설정 가능 (모델 지원 시)
        response = model.generate_content(prompt)
        # 단순 텍스트 파싱 또는 구조화된 데이터 생성
        # 여기서는 테스트를 위해 하드코딩된 리스트를 반환하거나 Gemini의 응답을 활용합니다.
        return [
            {
                "title": "[테스트] 머신러닝 기반의 도시 교통 혼잡도 예측 모델 연구",
                "author": "김철수 외 2명",
                "abstract": "본 연구는 서울시 교차로 데이터를 활용하여 실시간 교통량을 예측하는 모델을 제안한다...",
                "link": "https://scienceon.kisti.re.kr/"
            },
            {
                "title": "[테스트] GIS 데이터를 활용한 스마트시티 대기질 모니터링 시스템 구축",
                "author": "이영희",
                "abstract": "도시 내 미세먼지 저감을 위해 센서 데이터와 GIS 위치 정보를 결합한 분석을 수행하였다...",
                "link": "https://scienceon.kisti.re.kr/"
            }
        ]
    except:
        return []

def get_scienceon_papers():
    """실제 API 호출 함수 (키가 있을 때만 작동)"""
    if not SCIENCEON_API_KEY:
        print("ScienceON API 키가 아직 없습니다. 테스트 모드로 전환합니다.")
        return get_mock_papers()

    url = "https://scienceon.kisti.re.kr/openapicall/openApiCall.jsp"
    params = {
        "version": "2.0",
        "action": "search",
        "api_key": SCIENCEON_API_KEY,
        "search_keyword": "Smart City AND (GIS OR Traffic OR Data)",
        "doc_type": "KO_ARTI",
        "display_count": "10",
        "call_type": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        # 실제 API 승인 후 구조에 맞게 파싱 로직 작동
        return [] # 승인 전이라 빈 리스트 반환 시 mock으로 전환되게 설계
    except:
        return get_mock_papers()

def run_research_agent():
    try:
        papers = get_scienceon_papers()
        if not papers:
            papers = get_mock_papers()

        prompt = f"""
        너는 도시 데이터 사이언스 학부 연구생이야.
        다음 논문 리스트를 보고 IT 전공자 관점에서 연구 노트를 마크다운으로 작성해줘.

        [출력 형식 규칙 — 반드시 준수]
        1. 📊, 🏙️, 💡, 🚀 같은 이모지를 적절히 사용해 가독성을 높일 것
        2. 핵심 수치·중요 개념은 **굵게(Bold)** 처리
        3. 주요 섹션은 반드시 ### 마크다운 헤더 사용
        4. 불필요한 서론·맺음말 없이 본문만 출력
        5. 분석은 IT 전공자(데이터/개발 관점) 기준으로 작성
        
        ---
        
        ### 📊 오늘의 연구 논문 개요
        아래 표를 최상단에 배치해 핵심 정보를 요약해줘.
        
        | 구분 | 내용 |
        |---|---|
        | 분석 논문 수 | **N편** |
        | 주요 키워드 | 스마트시티, 도시환경, 데이터 |
        | 데이터 유형 | 정형 / 비정형 |
        
        ---
        
        ### 🏙️ Part 1. 연구 요약
        - 논문의 공통 주제와 연구 목적을 간결하게 정리
        - 도시 문제를 **데이터로 어떻게 정의했는지** 중심으로 설명
        
        ---
        
        ### 💻 Part 2. 사용 데이터 & 기술
        - 사용된 **데이터 종류**, **분석 기법**, **IT 기술 스택**을 정리
        - 예: 센서 데이터, 공공데이터, 머신러닝, 통계 분석 등
        
        ---
        
        ### 🚀 Part 3. IT 관점 인사이트
        - IT 전공자 입장에서 본 시사점 3가지 이상
        - 실제 서비스/시스템으로 확장 가능성
        - 기술적 한계나 개선 포인트가 있다면 함께 언급
        
        ---
        
        [분석 대상 논문 리스트]
        {papers}
        """

        response = model.generate_content(prompt)

        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)

        today_file = now.strftime("%Y-%m-%d")
        today_title = now.strftime("%Y/%m/%d")

        file_name = f"_posts/{today_file}-it-research.md"
        os.makedirs("_posts", exist_ok=True)

        with open(file_name, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write("layout: single\n")
            f.write(f"title: \"[Research] {today_title} 도시·환경 IT 연구 노트\"\n")
            f.write(f"date: {today_file}\n")
            f.write("categories: [it-research]\n")
            f.write("permalink: /it-research/{today_file}/\n")
            f.write("---\n\n")
            f.write(response.text)

        print(f"발행 완료: {file_name}")

    except Exception as e:
        print(f"에러: {e}")

if __name__ == "__main__":
    run_research_agent()
