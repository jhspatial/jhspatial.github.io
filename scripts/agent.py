import os
import google.generativeai as genai
import requests
from datetime import datetime

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# 모델명을 확실하게 'gemini-1.5-flash-latest'로 변경
model = genai.GenerativeModel('gemini-1.5-flash')


def get_global_news():
    url = f"https://newsapi.org/v2/everything?q=AI+technology&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('articles', [])[:10]
    return []

def run_news_agent():
    articles = get_global_news()
    if not articles:
        print("뉴스를 가져오지 못했습니다.")
        return

    prompt = f"당신은 IT 에디터입니다. 다음 뉴스 중 3개를 골라 한국어로 요약하고 Jekyll 마크다운 형식으로 작성하세요: {articles}"
    
    # 생성 시도
    try:
        response = model.generate_content(prompt)
        ai_content = response.text
        
        today = datetime.now().strftime("%Y-%m-%d")
        file_name = f"_posts/{today}-daily-ai-news.md"
        
        front_matter = f"---\nlayout: post\ntitle: \"[AI Agent] 오늘의 글로벌 뉴스\"\ndate: {today}\n---\n\n"
        
        os.makedirs('_posts', exist_ok=True)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(front_matter)
            f.write(ai_content)
        print(f"작성 완료: {file_name}")
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    run_news_agent()
