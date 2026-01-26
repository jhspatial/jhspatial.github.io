import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3
import json
import xmltodict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLIENT_ID = os.getenv("SCIENCEON_CLIENT_ID")
ACCESS_TOKEN = os.getenv("SCIENCEON_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scienceon_papers():
    url = "https://apigateway.kisti.re.kr/openapicall.do"
    
    # [핵심 1] 명세서 규칙 준수: JSON 덤프 시 공백 제거 (separators 사용)
    # 결과: {"BI":"스마트시티"} (띄어쓰기 없음) -> URL 인코딩 시 오류 최소화
    query_json = json.dumps({"BI": "스마트시티"}, separators=(',', ':'))
    
    params = {
        "client_id": CLIENT_ID,     # 필수: 64자리 ID
        "token": ACCESS_TOKEN,      # 필수: 액세스 토큰
        "version": "1.0",           # 필수: 버전
        "action": "search",         # [핵심 2] 사용자가 확인한 'search'
        "target": "ARTI",           # [핵심 3] 논문 대상 'ARTI'
        "searchQuery": query_json,  # [핵심 4] {"검색필드":"검색어"}
        "curPage": "1",
        "rowCount": "5"
    }
    
    try:
        # requests가 자동으로 searchQuery 값을 URI 인코딩해줍니다.
        response = requests.get(url, params=params, verify=False, timeout=15)
        
        print(f"DEBUG: Status Code: {response.status_code}")
        # 실제 요청된 URL을 확인해서 인코딩이 잘 되었는지 로그로 확인 가능
        print(f"DEBUG: Requested URL (Encoded): {response.url}") 
        
        if response.status_code != 200:
            print(f"DEBUG: API Error: {response.text[:200]}")
            return []

        # XML 파싱
        data_dict = xmltodict.parse(response.text)
        
        # ---------------------------------------------------------
        # [핵심 5] 만능 탐색 로직 (구조가 달라도 Title은 무조건 찾는다)
        # ---------------------------------------------------------
        def recursive_find(data, target_keys):
            found = []
            if isinstance(data, dict):
                for k, v in data.items():
                    if k.lower() in target_keys:
                        found.append(v)
                    else:
                        found.extend(recursive_find(v, target_keys))
            elif isinstance(data, list):
                for item in data:
                    found.extend(recursive_find(item, target_keys))
            return found

        titles = recursive_find(data_dict, ['title', 'article_title'])
        authors = recursive_find(data_dict, ['author', 'author_name'])
        abstracts = recursive_find(data_dict, ['abstract', 'abst'])
        
        if not titles:
            # 데이터가 200 OK인데 내용이 없으면 XML 구조를 로그에 찍어서 확인
            print("DEBUG: 검색 결과 없음. XML 원본 확인:")
            print(response.text[:1000]) 
            return []

        paper_list = []
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
        print("DEBUG: 데이터 수집 실패. (로그를 확인해주세요)")
        prompt = """
        너는 도시 데이터 사이언스 학부 연구생이야.
        ScienceON API 연동 문제로 실제 데이터 대신,
        '도시 데이터 분석'과 'LLM'의 결합 활용 사례 3가지를 정리해줘.
        """
    else:
        print(f"DEBUG: 성공! {len(papers)}건의 논문 데이터 수집: {[p['title'] for p in papers]}")
        prompt = f"다음 ScienceON 논문 검색 결과를 바탕으로 도시 환경 데이터 연구 노트를 작성해줘: {papers}"

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