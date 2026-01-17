import os
import google.generativeai as genai
import requests
from datetime import datetime

# 1. API 키 설정 (GitHub Secrets에서 불러옴)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # 무료이면서 성능이 좋은 모델

# 2. 해외 뉴스 수집 함수 (NewsAPI)
def get_global_news():
    # 'AI technology' 키워드로 최신 영어 뉴스 10개 수집
    url = f"https://newsapi.org/v2/everything?q=AI+technology&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json().get('articles', [])[:10]
    else:
        print(f"NewsAPI 호출 실패: {response.status_code}")
        return []

# 3. 에이전트 실행 함수 (Reasoning & Writing)
def run_news_agent():
    articles = get_global_news()
    if not articles:
        print("수집된 뉴스가 없습니다.")
        return

    # 에이전트에게 내리는 구체적인 페르소나와 지시사항 (Prompt)
    prompt = f"""
    너는 나의 개인 IT 기술 블로그를 운영하는 '전문 AI 에디터'야. 
    제공된 10개의 뉴스 리스트 중에서 한국 IT 종사자들이나 학생들에게 가장 영감을 줄 만한 뉴스 3개를 선정해줘.
    
    각 뉴스에 대해 아래 형식을 지켜서 작성해:
    1. 제목: 한국어로 흥미롭게 번역 (예: 단순히 직역하지 말고 클릭하고 싶게)
    2. 요약: 핵심 내용을 한국어로 3줄 요약
    3. 인사이트: 이 뉴스가 왜 중요한지 에디터로서의 짧은 의견 (1줄)
    4. 원문 링크: [Original Article] 형태
    
    결과는 Jekyll 블로그에서 바로 쓸 수 있게 마크다운(Markdown) 형식으로 작성해.
    뉴스 리스트: {articles}
    """
    
    # Gemini를 통한 결과 생성
    response = model.generate_content(prompt)
    ai_content = response.text
    
    # 4. Jekyll 포스팅 파일 생성
    # 파일명 형식: YYYY-MM-DD-title.md
    today = datetime.now().strftime("%Y-%m-%d")
    file_name = f"_posts/{today}-daily-ai-news.md"
    
    # Jekyll Front Matter (제목, 날짜, 레이아웃 설정)
    front_matter = f"""---
layout: post
title: "[AI Agent] 오늘의 글로벌 테크 뉴스 큐레이션"
date: {today}
categories: AI News
---

"""
    
    # 파일 저장 (기존 _posts 폴더에 저장됨)
    # 만약 폴더가 없으면 에러가 날 수 있으니 생성 확인 로직 추가
    os.makedirs('_posts', exist_ok=True)
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(front_matter)
        f.write(ai_content)
    
    print(f"성공적으로 포스팅을 생성했습니다: {file_name}")

if __name__ == "__main__":
    run_news_agent()
