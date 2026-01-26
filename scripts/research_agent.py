import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# 1. API 설정 (GitHub Secrets에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 등록 필요)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_naver_papers():
    """네이버 전문자료(학술논문 등) 검색"""
    url = "https://openapi.naver.com/v1/search/doc.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    # 스마트시티, 교통 데이터, 지능형 로보틱스 관련 키워드 검색
    params = {
        "query": "스마트시티 교통 데이터 분석",
        "display": 5,
        "start": 1,
        "sort": "sim"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            paper_list = []
            for item in items:
                # HTML 태그 제거 및 텍스트 정제
                title = item['title'].replace("<b>", "").replace("</b>", "")
                desc = item['description'].replace("<b>", "").replace("</b>", "")
                paper_list.append({
                    "title": title,
                    "link": item['link'],
                    "description": desc
                })
            return paper_list
        return []
    except:
        return []

def run_research_agent():
    papers = get_naver_papers()
    
    # 데이터가 있을 경우 Gemini에게 상세 분석 요청
    if papers:
        prompt = f"""
        너는 '도시 데이터 사이언스'를 전공하는 학부 연구생이야. 
        아래 수집된 최신 전문자료(논문/보고서) 리스트를 보고 IT 전공자 관점에서 연구 노트를 작성해줘.

        [수집된 데이터]
        {papers}

        [출력 규칙 - 반드시 준수]
        1. 형식: 마크다운 헤더(###)와 이모지(📊, 🏙️, 💻, 🚀) 활용
        2. 내용: 
           - 각 논문의 **제목**과 **출처 링크**를 명시할 것
           - IT/데이터 관점(데이터 수집 기법, 분석 모델 등)에서 분석할 것
           - 데이터가 아니어도 이쪽 도메인을 공부하려면 어떤 걸 더 공부하면 좋겠다 이런 걸 알려줘
        3. 서론/결론 없이 본문만 출력
        """
    else:
        # 데이터가 없을 때의 대비책
        prompt = "최근 스마트시티 교통 데이터 사이언스 및 지능형 로보틱스 분야의 IT 기술 트렌드에 대해 학부 연구생 관점에서 연구 노트를 작성해줘."

    response = model.generate_content(prompt)

    # 날짜 설정
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today_file = now.strftime("%Y-%m-%d")
    today_title = now.strftime("%Y/%m/%d")

    os.makedirs("_posts", exist_ok=True)
    file_name = f"_posts/{today_file}-urban-research.md"

    # 블로그 Front Matter 설정 (기존 형식 유지)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("layout: single\n")
        f.write(f"title: \"[Research] {today_title} 도시·환경 IT 연구 노트\"\n")
        f.write(f"date: {today_file}\n")
        f.write("categories: [research]\n") # 요청하신 카테고리 유지
        f.write("---\n\n")
        f.write(response.text)
    
    print(f"발행 완료: {file_name}")

if __name__ == "__main__":
    run_research_agent()
