import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3
import json
import xmltodict  # XML 변환용 추가

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLIENT_ID = os.getenv("SCIENCEON_CLIENT_ID")
ACCESS_TOKEN = os.getenv("SCIENCEON_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scienceon_papers():
    url = "https://apigateway.kisti.re.kr/openapicall.do"
    query_json = json.dumps({"BI": "스마트시티"})
    
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
            return []

        # 200인데 JSON 에러가 난다면 100% XML입니다.
        # XML을 딕셔너리로 변환
        data_dict = xmltodict.parse(response.text)
        
        # ScienceON XML 구조: MetaData > recordList > record 리스트
        paper_list = []
        try:
            # XML 구조를 따라가며 데이터 추출
            metadata = data_dict.get('MetaData', {})
            record_list = metadata.get('recordList', {})
            records = record_list.get('record', [])
            
            # 검색 결과가 1개일 경우 리스트가 아닐 수 있으므로 처리
            if isinstance(records, dict):
                records = [records]

            for rec in records:
                # XML의 항목명은 대문자로 시작하는 경우가 많습니다 (가이드 기준)
                paper_list.append({
                    "title": rec.get('Title'),
                    "author": rec.get('Author'),
                    "abstract": rec.get('Abstract') or "초록 없음"
                })
        except Exception as parse_e:
            print(f"DEBUG: XML Parsing Error: {parse_e}")
            # 구조가 다를 경우를 대비해 원본 로그 출력 (디버깅용)
            # print(response.text) 
            
        return paper_list
    except Exception as e:
        print(f"DEBUG: General Error: {e}")
        return []

def run_research_agent():
    papers = get_scienceon_papers()
    
    if not papers:
        print("DEBUG: 실제 데이터를 찾지 못해 트렌드 리포트를 작성합니다.")
        prompt = "도시 데이터 사이언스 전공자 관점에서 최근 '스마트시티'와 '지능형 로보틱스'의 결합 트렌드에 대해 연구 노트를 작성해줘."
    else:
        print(f"DEBUG: {len(papers)}건의 논문 데이터를 찾았습니다.")
        prompt = f"다음 논문 리스트를 IT 전공자 관점에서 연구 노트로 요약해줘: {papers}"

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