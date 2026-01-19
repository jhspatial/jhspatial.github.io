import os
import requests
import glob
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)

def get_naver_exchange_news():
    """네이버 API를 통해 환율 분석 뉴스를 수집합니다."""
    # 원달러와 원엔 환율 원인 분석을 위한 키워드 검색
    queries = ["원달러 환율 원인 분석", "원엔 환율 전망 원인"]
    collected_news = []
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    for query in queries:
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&sort=sim"
        try:
            res = requests.get(url, headers=headers)
            items = res.json().get('items', [])
            collected_news.extend(items)
        except Exception as e:
            print(f"네이버 API 호출 에러 ({query}): {e}")
            
    return collected_news

def get_global_it_news():
    """NewsAPI를 통해 글로벌 IT/AI 뉴스를 수집합니다."""
    url = f"https://newsapi.org/v2/everything?q=AI+technology+trend&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        return res.json().get('articles', [])[:10]
    except Exception as e:
        print(f"NewsAPI 호출 에러: {e}")
        return []

def get_memory():
    """어제 작성한 글의 내용을 읽어옵니다 (중복 방지 및 문맥 유지)."""
    try:
        list_of_files = glob.glob('_posts/*.md')
        if not list_of_files:
            return "이전 기록이 없습니다. 오늘이 첫 발행입니다."
        latest_file = sorted(list_of_files)[-1]
        with open(latest_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"기억 읽기 실패: {e}"

def run_news_agent():
    # 1. 데이터 수집 (네이버 환율뉴스 + 글로벌 IT뉴스 + 어제 기억)
    exchange_data = get_naver_exchange_news()
    it_news_data = get_global_it_news()
    memory = get_memory()

    # 2. 모델 설정 (Gemini 2.0 Flash)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 3. 프롬프트 구성 (두 가지 정보를 통합 분석)
    prompt = f"""
    너는 경제 애널리스트이자 IT 전문 에디터야. 
    오늘 수집된 [환율 데이터]와 [IT 뉴스]를 바탕으로 한국 독자들을 위한 종합 리포트를 작성해줘.

    [어제의 기록 (중복 금지)]
    {memory}

    [섹션 1: 실시간 환율 및 원인 분석 (네이버 데이터 기준)]
    데이터: {exchange_data}
    - 원/달러 및 원/엔 환율의 현재 흐름을 요약해줘.
    - 뉴스에 언급된 환율 변동의 구체적인 '원인'을 심도 있게 분석해줘.

    [섹션 2: 오늘의 글로벌 IT/AI 헤드라인 (NewsAPI 데이터 기준)]
    데이터: {it_news_data}
    - 가장 중요한 IT 뉴스 3가지를 선정해줘.
    - {memory}에 언급된 소식과 중복되지 않아야 해.
    - 각 뉴스별 핵심 요약과 경제적 관점에서의 통찰력을 덧붙여줘.

    [작성 가이드라인]
    - 말투: 전문적이고 신뢰감 있는 한국어 (~입니다).
    - 독자층: 경제와 기술의 상관관계에 관심이 많은 한국 독자.
    - 출력 형식: Jekyll 마크다운 본문만 (Front Matter 제외).
    """

    try:
        response = model.generate_content(prompt)
        
        # 한국 시간(KST) 설정
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        today_file = now.strftime("%Y-%m-%d")
        today_title = now.strftime("%Y/%m/%d")

        # 파일 저장
        file_name = f"_posts/{today_file}-daily-briefing.md"
        os.makedirs('_posts', exist_ok=True)
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: single\n")
            f.write(f"title: \"{today_title} 경제 환율 & IT 뉴스 브리핑\"\n")
            f.write(f"date: {today_file}\n")
            f.write(f"categories: [daily-news]\n")
            f.write(f"---\n\n")
            f.write(response.text)
            
        print(f"발행 완료: {file_name}")

    except Exception as e:
        print(f"에이전트 실행 에러: {e}")

if __name__ == "__main__":
    run_news_agent()
