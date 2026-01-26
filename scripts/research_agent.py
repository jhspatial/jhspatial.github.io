import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3
import json
import xmltodict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLIENT_ID = os.getenv("SCIENCEON_CLIENT_ID")
ACCESS_TOKEN = os.getenv("SCIENCEON_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def recursive_find(data, target_keys):
    """딕셔너리/리스트 깊숙한 곳까지 뒤져서 특정 키의 값을 찾아내는 함수"""
    found = []
    if isinstance(data, dict):
        for k, v in data.items():
            # 키 이름이 타겟과 일치하면(대소문자 무시) 저장
            if k.lower() in target_keys:
                found.append(v)
            else:
                found.extend(recursive_find(v, target_keys))
    elif isinstance(data, list):
        for item in data:
            found.extend(recursive_find(item, target_keys))
    return found

def get_scienceon_papers():
    url = "https://apigateway.kisti.re.kr/openapicall.do"
    
    # 쿼리: 가장 확실한 키워드로 테스트
    query_json = json.dumps({"BI": "인공지능"})
    
    params = {
        "client_id": CLIENT_ID,
        "token": ACCESS_TOKEN,
        "version": "1.0",
        "action": "search",
        "target": "ARTI",
        "searchQuery": query_json,
        "curPage": "1",
        "rowCount": "5"
    }
    
    try:
        response = requests.get(url, params=params, verify=False, timeout=15)
        print(f"DEBUG: Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"DEBUG: API Error: {response.text[:200]}")
            return []

        # [중요] 디버깅을 위해 원본 데이터 앞부분만 로그에 출력
        # 만약 이번에도 실패하면 이 로그를 보고 구조를 바로 알 수 있습니다.
        print(f"DEBUG: Raw XML Start: {response.text[:300]}...") 

        # XML -> Dictionary 변환
        data_dict = xmltodict.parse(response.text)
        
        # 구조를 몰라도 'Title'이나 'article_title'이라는 키를 가진 놈을 다 찾아냄
        titles = recursive_find(data_dict, ['title', 'article_title'])
        authors = recursive_find(data_dict, ['author', 'author_name'])
        abstracts = recursive_find(data_dict, ['abstract', 'abst'])
        
        paper_list = []
        # 찾은 제목 개수만큼 리스트 생성 (최대 5개)
        for i in range(min(len(titles), 5)):
            paper_list.append({
                "title": titles[i],
                "author": authors[i] if i < len(authors) else "저자 미상",
                "abstract": abstracts[i] if i < len(abstracts) else "초록 없음"
            })
            
        return paper_list

    except Exception as e:
        print(f"DEBUG: Critical Error: {e}")
        return []

def run_research_agent():
    papers = get_scienceon_papers()
    
    if not papers:
        print("DEBUG: 데이터 추출 실패. (로그의 Raw XML Start를 확인하세요)")
        # 데이터가 없을 때도 블로그 글은 발행되도록 트렌드 주제 설정
        prompt = """
        너는 도시 데이터 사이언스 연구원이야. 
        API 데이터 수집에 일시적 문제가 생겼어. 
        대신 '생성형 AI와 도시 계획(Urban Planning)'의 최신 융합 사례 3가지를 정리해줘.
        """
    else:
        print(f"DEBUG: 성공! {len(papers)}건의 논문을 찾았습니다: {[p['title'] for p in papers]}")
        prompt = f"다음 논문 리스트를 바탕으로 IT 전공자 관점의 연구 노트를 작성해줘: {papers}"

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