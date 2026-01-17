import os
import google.generativeai as genai
import requests
from datetime import datetime

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

def run_news_agent():
    # 1. 뉴스 수집
    url = f"https://newsapi.org/v2/everything?q=AI+technology&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        articles = res.json().get('articles', [])[:10]
    except Exception as e:
        print(f"뉴스 수집 에러: {e}")
        return

    if not articles:
        print("뉴스를 가져오지 못했습니다.")
        return

    # 2. 모델 설정 (안정적인 gemini-1.5-flash 권장)
    model_name = 'gemini-2.5-flash' 
    model = genai.GenerativeModel(model_name)

    # 3. 프롬프트 설정
    prompt = f"""
    너는 기술 전문 블로그 'IT 인사이트'를 운영하는 전문 에디터야. 
    아래 전달받은 10개의 최신 AI 뉴스 리스트를 분석해서, 한국 독자들이 꼭 알아야 할 '오늘의 TOP 3' 뉴스를 선정해줘.

    [작성 가이드라인]
    1. 말투: 독자들에게 지식을 전달하는 차분하고 신뢰감 있는 어조 (~입니다, ~합니다).
    2. 제목: 단순 번역이 아닌, 호기심을 자극하는 매력적인 국문 제목으로 가공해줘.
    3. 구성 (각 뉴스별):
       - 📌 **핵심 요약**: 뉴스 내용을 전문적으로 3문장 이내로 요약.
       - 💡 **전문가 견해**: 이 뉴스가 향후 AI 산업이나 우리 삶에 어떤 영향을 줄지 에디터의 통찰력을 한 문장으로 추가.
       - 🔗 **관련 링크**: [원문 읽기](URL) 형식.
    
    [출력 형식]
    Jekyll 블로그에 바로 올릴 수 있도록 마크다운(Markdown) 문법을 사용해.
    Front Matter(--- 부분)는 제외하고 본문 마크다운만 출력해줘.
    각 뉴스 사이에는 구분선(---)을 넣어줘.

    뉴스 리스트: {articles}
    """
    
    try:
        response = model.generate_content(prompt)
        
        # 날짜 데이터 생성
        now = datetime.now()
        today_file = now.strftime("%Y-%m-%d")    
        today_title = now.strftime("%Y/%m/%d")   
        
        # 파일 경로 설정
        file_name = f"_posts/{today_file}-daily-ai-news.md"
        os.makedirs('_posts', exist_ok=True)
        
        # 4. 파일 저장
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: single\n")
            f.write(f"title: \"{today_title} AI NEWS\"\n")
            f.write(f"date: {today_file}\n")
            f.write(f"categories: [daily-news]\n")
            f.write(f"---\n\n")
            f.write(response.text)
            
        print(f"성공적으로 발행되었습니다: {file_name}")
        
    except Exception as e:
        print(f"에이전트 실행 에러: {e}")

if __name__ == "__main__":
    run_news_agent()
