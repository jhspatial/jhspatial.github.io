import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
import glob
import re

# 1. API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_all_past_titles(target_category="research"):
    """
    _posts 폴더 내의 모든 파일을 확인하여,
    특정 카테고리에 속한 게시글의 '제목(Title)' 목록을 전부 반환합니다.
    """
    titles = []
    # 모든 md 파일 탐색
    files = glob.glob('_posts/*.md')
    
    # 카테고리 확인용 정규식 (research가 포함된 대괄호 찾기)
    category_pattern = re.compile(r"categories:\s*\[?[^\]\n]*" + re.escape(target_category) + r"[^\]\n]*\]?")
    # 제목 추출용 정규식 (title: "..." 또는 title: ... 형태)
    title_pattern = re.compile(r"title:\s*[\"']?([^\"'\n]+)[\"']?")

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                parts = content.split('---')
                
                if len(parts) >= 3:
                    front_matter = parts[1]
                    # 해당 카테고리인 경우에만 제목 추출
                    if category_pattern.search(front_matter):
                        match = title_pattern.search(front_matter)
                        if match:
                            # [Research] 태그 등이 있다면 제거하고 순수 제목만 남기는 것이 좋음 (선택사항)
                            clean_title = match.group(1).strip()
                            titles.append(clean_title)
        except Exception:
            continue
            
    return titles

def get_naver_papers():
    """네이버 전문자료(학술논문 등) 검색"""
    url = "https://openapi.naver.com/v1/search/doc.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    raw_query = '(urban|smart city|environment|traffic|data)'
    params = {
        "query": raw_query,
        "display": 50, # 비교 대상을 많이 가져옴
        "start": 1,
        "sort": "date"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            paper_list = []
            for item in items:
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
    # 1. 네이버에서 최신 논문 검색
    papers = get_naver_papers()
    
    # 2. 블로그에 이미 작성된 모든 글의 제목 가져오기
    past_titles = get_all_past_titles(target_category="research")
    
    # 날짜 설정
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today_file = now.strftime("%Y-%m-%d")
    today_display = now.strftime("%Y/%m/%d")

    # 이미 작성된 제목들을 문자열로 변환
    past_titles_str = "\n".join([f"- {t}" for t in past_titles]) if past_titles else "없음 (첫 글 작성)"

    if papers:
        prompt = f""" 
        너는 도시공학과 데이터 사이언스를 공부하는 IT 전공 3학년 학부 연구생이야.
        아래 [수집된 데이터] 목록에서 **블로그에 포스팅할 가장 가치 있는 논문 1개**를 선정해줘.

        [중복 방지 규칙 - 매우 중요!]
        아래 [이미 작성된 논문 목록]에 있는 제목과 겹치는 논문은 **절대 선정하지 마.**

        [이미 작성된 논문 목록]
        {past_titles_str}

        [수집된 데이터 (검색 결과)]
        {papers}

        [필수 요청 사항]
        1. **첫 줄 출력**: 맨 첫 줄에 `TITLE: 선정된 논문 제목` 형식으로 출력할 것. (이 제목이 블로그 글 제목이 됨)
        2. **본문 작성**: 둘째 줄부터 바로 마크다운 형식으로 분석 내용 작성.

        [작성 가이드라인]
        1. **독자 타겟**: 학부생 동기들이 이해할 수 있는 수준 (어려운 용어는 쉽게 풀어서 설명).
        2. **구성**:
            - **논문 원제 및 링크**: (정확한 출처 표기)
            - **🏙️ Problem (왜 중요해?)**: 도시 문제와의 연결고리.
            - **🔍 Solution (어떻게 풀었어?)**: 데이터와 방법론 (핵심 위주).
            - **💡 Result (결과는?)**: 시사점.
            - **🚀 Growth (더 공부할 것)**: 연관 키워드.
        """
    else:
        prompt = "스마트시티 관련 최신 논문이 검색되지 않았습니다. `TITLE: 스마트시티 기술 연구 동향` 으로 제목을 잡고 일반적인 최신 트렌드를 정리해줘."

    # Gemini 호출
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # --- 제목 추출 및 본문 분리 ---
    lines = raw_text.split('\n')
    final_title = f"{today_display} 도시·환경 IT 연구 노트"
    body_content = raw_text

    if lines and lines[0].startswith("TITLE:"):
        extracted_title = lines[0].replace("TITLE:", "").strip()
        final_title = extracted_title.replace('"', '').replace("'", "")
        body_content = "\n".join(lines[1:]).strip()
    
    # --- 파일 저장 ---
    os.makedirs("_posts", exist_ok=True)
    file_name = f"_posts/{today_file}-urban-research.md"
    slug = f"urban-research-{today_file}"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("layout: single\n")
        f.write(f"title: \"[Research] {final_title}\"\n") # AI가 뽑은 제목 사용
        f.write(f"date: {today_file}\n")
        f.write("categories: [research]\n")
        f.write(f"slug: \"{slug}\"\n")
        f.write("---\n\n")
        f.write(body_content)
    
    print(f"발행 완료: {file_name}")
    print(f"선정된 제목: {final_title}")
    print(f"제외된 과거 목록 개수: {len(past_titles)}개")

if __name__ == "__main__":
    run_research_agent()
