import os
import google.generativeai as genai
import requests
from datetime import datetime

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

def run_news_agent():
    # [중요] 사용 가능한 모델 리스트 출력 로직 추가
    print("--- 사용 가능한 모델 리스트 확인 ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"사용 가능 모델명: {m.name}")
    except Exception as e:
        print(f"모델 목록 확인 실패: {e}")

    # 1. 뉴스 수집
    url = f"https://newsapi.org/v2/everything?q=AI+technology&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    articles = requests.get(url).json().get('articles', [])[:10]
    
    if not articles:
        print("뉴스를 가져오지 못했습니다.")
        return

    # 2. 모델 선택 (에러가 가장 적은 gemini-1.5-flash 혹은 2.0-flash-exp 시도)
    # 아래 이름을 번갈아가며 시도해보세요.
    model_name = 'gemini-2.5-flash' 
    model = genai.GenerativeModel(model_name)

    # 3. 에이전트 작업
    prompt = f"당신은 IT 에디터입니다. 다음 뉴스를 요약해서 Jekyll 마크다운 형식으로 써주세요: {articles}"
    
    try:
        response = model.generate_content(prompt)
        
        # 1. 날짜 데이터 생성
        now = datetime.now()
        today_file = now.strftime("%Y-%m-%d")    # 파일명용 (2026-01-17)
        today_title = now.strftime("%Y/%m/%d")   # 제목용 (2026/01/17)
        
        # 2. 파일 경로 및 이름 설정
        file_name = f"_posts/{today_file}-daily-ai-news.md"
        os.makedirs('_posts', exist_ok=True)
        
        # 3. 파일 저장
        with open(file_name, "w", encoding="utf-8") as f:
            # title 부분에 today_title 변수를 삽입합니다.
            f.write(f"---\nlayout: single\ntitle: \"{today_title} AI NEWS\"\ndate: {today_file}\n---\n\n")
            f.write(response.text)
            
        print(f"성공적으로 발행되었습니다: {file_name}")
        
    except Exception as e:
        print(f"에이전트 실행 에러: {e}")

if __name__ == "__main__":
    run_news_agent()
