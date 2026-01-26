import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SCIENCEON_API_KEY = os.getenv("SCIENCEON_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scienceon_papers():
    url = "https://scienceon.kisti.re.kr/openapicall/openApiCall.jsp"
    params = {
        "version": "2.0",
        "action": "search",
        "api_key": SCIENCEON_API_KEY,
        "search_keyword": "스마트시티", # 단순한 키워드로 변경해봄
        "doc_type": "KO_ARTI",
        "display_count": "5",
        "call_type": "json"
    }
    
    try:
        response = requests.get(url, params=params, verify=False, timeout=15)
        print(f"DEBUG: Status Code: {response.status_code}")
        
        # [중요] API가 보낸 원본 데이터를 로그에 찍습니다. 
        # 나중에 GitHub Actions 로그에서 이 부분을 복사해서 저에게 알려주세요!
        print("DEBUG: Raw Response Start")
        print(response.text) 
        print("DEBUG: Raw Response End")

        data = response.json()
        
        # 데이터 추출 시도 (구조가 다를 것에 대비)
        paper_list = []
        # ScienceON의 실제 데이터는 보통 kisti_output -> item 리스트에 있습니다.
        output = data.get('kisti_output', {})
        items = output.get('item', [])

        if not items: # 만약 result 아래에 있다면?
            items = data.get('result', [])

        for item in items:
            paper_list.append({
                "title": item.get('title') or item.get('article_title'),
                "author": item.get('author') or item.get('author_name'),
                "abstract": item.get('abstract') or item.get('abst') or "초록 없음"
            })
        return paper_list
    except Exception as e:
        print(f"DEBUG: Error occurred: {e}")
        return []

def run_research_agent():
    papers = get_scienceon_papers()
    
    # API가 비어있으면 강제로 에러를 내서 로그를 보게 하거나, 
    # 혹은 이번에는 '진짜 데이터 없음'이라고 파일에 써버립시다.
    if not papers:
        content = "## ⚠️ API 데이터를 가져오지 못했습니다.\n로그를 확인하여 JSON 구조를 파악해야 합니다."
    else:
        prompt = f"다음 논문 리스트를 IT 전공자 관점에서 요약해줘: {papers}"
        response = model.generate_content(prompt)
        content = response.text

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today_file = now.strftime("%Y-%m-%d")
    
    os.makedirs("_posts", exist_ok=True)
    file_name = f"_posts/{today_file}-urban-research.md"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"---\nlayout: single\ntitle: \"[Research] {today_file} 테스트\"\n---\n\n")
        f.write(content)
    
    print(f"발행 완료: {file_name}")

if __name__ == "__main__":
    run_research_agent()
