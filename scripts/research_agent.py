import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# 1. 환경 변수에서 키 로드
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_naver_papers():
    # 네이버 전문자료(doc) 검색 엔드포인트
    url = "https://openapi.naver.com/v1/search/doc.json"
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    # 3학년 전공생 수준에 맞는 키워드로 검색
    params = {
        "query": "스마트시티 교통 데이터 분석 논문",
        "display": 5, # 5개 출력
        "start": 1,
        "sort": "sim"  # 유사도순
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            paper_list = []
            for item in items:
                # <b> 태그 제거 등 텍스트 정제
                clean_title = item['title'].replace("<b>", "").replace("</b>", "")
                clean_desc = item['description'].replace("<b>", "").replace("</b>", "")
                paper_list.append({
                    "title": clean_title,
                    "description": clean_desc,
                    "link": item['link']
                })
            return paper_list
        else:
            print(f"DEBUG: Naver API Error {response.status_code}")
            return []
    except Exception as e:
        print(f"DEBUG: Error - {e}")
        return []

def run_research_agent():
    papers = get_naver_papers()
    
    # 데이터 수집 결과에 따른 프롬프트 (도시 데이터 RA 컨셉)
    if not papers:
        prompt = """
        너는 도시 데이터 사이언스 학부 연구생이야. 
        오늘은 검색 결과가 없어서 '지능형 로보틱스와 도시 교통의 미래'에 대한 
        본인의 연구 견해를 마크다운 형식으로 작성해줘.
        """
    else:
        prompt = f"""
        너는 도시 데이터 사이언스 학술 블로거이자 학부 연구생이야. 
        아래 검색된 전문자료(논문) 리스트를 보고 IT 전공자 관점에서 연구 노트를 작성해줘.
        
        [검색 데이터]
        {papers}
        
        [작성 가이드]
        - 📊 오늘의 연구 개요 (표 형식)
        - 🏙️ 주요 연구 요약
        - 💻 IT/데이터 관점의 핵심 기술 분석
        - 🚀 한계점 및 향후 연구 방향 (연구생의 시각)
        """

    response = model.generate_content(prompt)

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today_file = now.strftime("%Y-%m-%d")
    
    os.makedirs("_posts", exist_ok=True)
    file_name = f"_posts/{today_file}-urban-research.md"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"---\nlayout: single\ntitle: \"[Research] {now.strftime('%Y/%m/%d')} 도시 데이터 IT 연구 노트\"\n---\n\n")
        f.write(response.text)
    
    print(f"발행 완료: {file_name}")

if __name__ == "__main__":
    run_research_agent()