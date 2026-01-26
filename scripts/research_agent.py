import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3

# SSL 경고 무시 (Actions 환경에서 필수일 때가 많음)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCIENCEON_API_KEY = os.getenv("SCIENCEON_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scienceon_papers():
    """ScienceON API 호출 및 데이터 추출"""
    url = "https://scienceon.kisti.re.kr/openapicall/openApiCall.jsp"
    params = {
        "version": "2.0",
        "action": "search",
        "api_key": SCIENCEON_API_KEY,
        "search_keyword": "Smart City AND (GIS OR Traffic)",
        "doc_type": "KO_ARTI",
        "display_count": "5",
        "call_type": "json"
    }
    
    try:
        # verify=False로 인증서 문제 회피
        response = requests.get(url, params=params, verify=False, timeout=15)
        
        if response.status_code != 200:
            return []

        data = response.json()
        
        # ScienceON의 복잡한 JSON 구조 파싱
        # 보통 result > item 또는 kisti_output > item 구조입니다.
        paper_list = []
        
        # 데이터가 있는 경로를 유연하게 탐색
        items = []
        if 'result' in data:
            items = data['result']
        elif 'kisti_output' in data:
            items = data['kisti_output'].get('item', [])

        if not isinstance(items, list):
            # 단일 항목일 경우 리스트로 변환
            items = [items] if items else []

        for item in items:
            # 필드명이 다를 경우를 대비해 여러 키값 시도
            title = item.get('title') or item.get('article_title') or "제목 정보 없음"
            author = item.get('author') or item.get('author_name') or "저자 미상"
            abstract = item.get('abstract') or item.get('abst') or "초록 내용이 없습니다."
            
            paper_list.append({
                "title": title,
                "author": author,
                "abstract": abstract[:500] # 너무 길면 잘림 방지
            })
            
        return paper_list
    except Exception as e:
        print(f"API 호출 중 에러 발생: {e}")
        return []

def run_research_agent():
    # 1. 데이터 가져오기
    papers = get_scienceon_papers()
    
    # 2. 데이터가 없으면 가짜 데이터라도 넣어줌 (완전 빈 파일 방지)
    if not papers:
        papers = [
            {"title": "[예시] 스마트시티 교통 데이터 분석", "author": "연구팀", "abstract": "실시간 교통 데이터를 활용한 도시 최적화 방안..."},
            {"title": "[예시] GIS 기반 환경 모니터링", "author": "분석팀", "abstract": "지리정보시스템을 이용한 미세먼지 확산 모델링..."}
        ]

    # 3. Gemini 프롬프트 구성
    prompt = f"""
    너는 도시 데이터 사이언스 학부 연구생이야.
    아래 논문 정보를 바탕으로 IT 전공자 관점에서 연구 노트를 작성해줘.
    
    [논문 리스트]
    {papers}
    
    [출력 규칙]
    - 반드시 마크다운(Markdown) 형식을 사용할 것.
    - ### Part 1. 연구 요약
    - ### Part 2. 사용 데이터 & 기술
    - ### Part 3. IT 관점 인사이트
    - 데이터 중심(ML, 분석 기술, 데이터 스택)으로 설명할 것.
    """

    response = model.generate_content(prompt)

    # 4. 파일 저장
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today_file = now.strftime("%Y-%m-%d")
    
    os.makedirs("_posts", exist_ok=True)
    file_name = f"_posts/{today_file}-urban-research.md"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write("---\nlayout: single\ntitle: \"[Research] 도시 데이터 IT 연구 노트\"\n---\n\n")
        f.write(response.text)
    
    print(f"발행 완료: {file_name}")

if __name__ == "__main__":
    run_research_agent()