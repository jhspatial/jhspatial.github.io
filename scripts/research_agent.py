import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import urllib3
import json
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. API 설정 (GitHub Secrets에 맞게 확인)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLIENT_ID = os.getenv("SCIENCEON_CLIENT_ID") # 64자리 영문숫자 ID
ACCESS_TOKEN = os.getenv("SCIENCEON_API_KEY") # 발급받은 토큰값

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scienceon_papers():
    # 가이드에 명시된 새로운 호출 주소
    url = "https://apigateway.kisti.re.kr/openapicall.do"
    
    # searchQuery를 JSON 형식으로 구성 후 인코딩
    query_json = json.dumps({"BI": "스마트시티"})
    
    params = {
        "client_id": CLIENT_ID,
        "token": ACCESS_TOKEN,
        "version": "1.0",
        "action": "search",
        "target": "ARTI",
        "searchQuery": query_json, # {"BI":"스마트시티"}
        "curPage": "1",
        "rowCount": "5"
    }
    
    try:
        # GET 요청 시 params 전달
        response = requests.get(url, params=params, verify=False, timeout=15)
        print(f"DEBUG: Status Code: {response.status_code}")
        
        # 404 에러 방지용 로그
        if response.status_code != 200:
            print(f"DEBUG: Error Response: {response.text[:200]}")
            return []

        # 가이드상 응답은 XML 또는 JSON인데, 보통 MetaData 태그로 시작함
        # 만약 JSON으로 요청했다면 아래와 같이 파싱
        data = response.json()
        
        # 가이드 문서 샘플 구조: MetaData > resultSummary > ...
        # 실제 데이터는 데이터 구조에 따라 보정이 필요할 수 있습니다.
        paper_list = []
        
        # JSON 응답 내에서 논문 아이템 추출 시도
        # (가이드에는 XML 샘플만 있지만, 보통 record나 item 키를 사용함)
        records = data.get('MetaData', {}).get('recordList', {}).get('record', [])
        if isinstance(records, dict): records = [records]

        for rec in records:
            paper_list.append({
                "title": rec.get('Title') or rec.get('title'),
                "author": rec.get('Author') or rec.get('author'),
                "abstract": rec.get('Abstract') or rec.get('abstract') or "초록 없음"
            })
            
        return paper_list
    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        return []

def run_research_agent():
    papers = get_scienceon_papers()
    
    # 데이터가 없으면 트렌드 리포트로 대체 (안정적인 동작)
    if not papers:
        print("DEBUG: API 데이터 수집 실패. 최신 동향으로 대체 생성합니다.")
        prompt = "최근 '스마트시티 및 교통 데이터 사이언스' 관련 주요 IT 기술 트렌드 3가지를 학부 연구생 관점에서 마크다운으로 작성해줘."
    else:
        prompt = f"다음 논문 데이터를 바탕으로 IT 전공자 관점의 연구 노트를 작성해줘: {papers}"

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