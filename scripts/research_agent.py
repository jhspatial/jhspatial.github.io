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
    raw_query = '(smart city | urban) (environment | traffic | "data")'
    # 스마트시티, 교통 데이터, 지능형 로보틱스 관련 키워드 검색
    params = {
        "query": raw_query,
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
        너는 복잡한 연구 내용을 학부생도 이해하기 쉽게 풀어서 설명해주는 '친절한 전공 멘토'야. 
        도시와 환경에 관심이 많은 IT 전공 3학년 학생이 블로그에 기록할 수 있도록, 아래 논문 리스트를 알기 쉽게 정리해줘.

        [수집된 데이터]
        {papers}

        [작성 가이드라인]
        1. **쉬운 설명**: 어려운 학술적 용어보다는 일상적인 비유나 쉬운 단어를 사용해. (예: '열섬 현상' -> '도시가 주변보다 뜨거워지는 현상')
        2. **구성 요소**:
            - **제목 및 링크**: 논문의 제목과 바로가기 링크.
            - **🏙️ 이 논문은 왜 썼을까? (Problem)**: 이 연구가 해결하려는 실제 도시/환경의 문제가 무엇인지, 왜 중요한지 설명해줘.
            - **🔍 어떻게 해결했을까? (Solution)**: 복잡한 수식보다는 '어떤 데이터를 써서 어떤 과정을 거쳤는지' 흐름 위주로 알려줘.
            - **💡 결과가 뭐야? (Result)**: 이 연구를 통해 새롭게 알게 된 사실이나 세상이 어떻게 바뀔 수 있는지 요약해줘.
            - **🚀 한 걸음 더! (Growth Guide)**: 이 논문의 주제가 흥미롭다면, 다음에 어떤 키워드를 검색해보거나 어떤 이론을 더 찾아보면 좋을지 가이드라인을 줘.

        [출력 규칙]
        - 서론/결론 없이 바로 본문 내용을 출력할 것.
        - 각 논문은 구분선(---)으로 명확히 나눌 것.
        - 3학년 수준에서 충분히 이해할 수 있는 친절한 말투를 유지할 것.
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
