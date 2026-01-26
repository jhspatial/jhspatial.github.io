import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCIENCEON_API_KEY = os.getenv("SCIENCEON_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scienceon_papers():
    # URL 주소 확인 (ScienceON Open API 표준 주소)
    url = "https://scienceon.kisti.re.kr/openapicall/openApiCall.jsp"
    
    params = {
        "version": "2.0",
        "action": "search",
        "target": "ARTI",       # [중요] 검색 대상(논문: ARTI) 필수 추가
        "api_key": SCIENCEON_API_KEY,
        "search_keyword": "스마트시티",
        "display_count": "5",
        "call_type": "json"     # 결과 포맷
    }
    
    try:
        # GET 요청 시 params를 명확히 전달
        response = requests.get(url, params=params, verify=False, timeout=15)
        
        print(f"DEBUG: Status Code: {response.status_code}")
        
        # 404가 뜨면 URL이 잘못된 것이므로 예비 데이터를 반환
        if response.status_code != 200:
            print("DEBUG: API URL or Parameter error (404/500)")
            return []

        data = response.json()
        
        # ScienceON JSON 구조: kisti_output > item 리스트
        output = data.get('kisti_output', {})
        items = output.get('item', [])

        # 만약 리스트가 아니라 단일 딕셔너리면 리스트로 감싸줌
        if isinstance(items, dict):
            items = [items]

        paper_list = []
        for item in items:
            # 필드명 매핑 (ScienceON은 보통 한글 필드명을 쓰기도 함)
            title = item.get('title') or item.get('article_title') or "제목 없음"
            author = item.get('author') or item.get('author_name') or "저자 미상"
            abstract = item.get('abstract') or item.get('abst') or "초록 없음"
            
            paper_list.append({
                "title": title,
                "author": author,
                "abstract": abstract[:500]
            })
        return paper_list

    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        return []

def run_research_agent():
    papers = get_scienceon_papers()
    
    # 데이터가 비어있을 때 프롬프트를 다르게 줘서 '가짜 데이터' 방지
    if not papers:
        # 404 에러 등으로 데이터를 못 가져왔을 때의 폴백(Fallback) 로직
        print("DEBUG: No data from API, using default topic.")
        prompt = "현재 스마트시티와 GIS 데이터 분석 분야의 최신 연구 동향 3가지를 학부 연구생 관점에서 정리해줘."
    else:
        prompt = f"다음 논문 리스트를 보고 IT 전공자 관점에서 연구 노트를 작성해줘: {papers}"

    response = model.generate_content(prompt)

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today_file = now.strftime("%Y-%m-%d")
    
    os.makedirs("_posts", exist_ok=True)
    file_name = f"_posts/{today_file}-urban-research.md"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"---\nlayout: single\ntitle: \"[Research] {now.strftime('%Y/%m/%d')} 도시 데이터 연구 노트\"\n---\n\n")
        f.write(response.text)
    
    print(f"발행 완료: {file_name}")

if __name__ == "__main__":
    run_research_agent()