import os
import requests
import glob
import yfinance as yf
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)

def get_realtime_exchange():
    """야후 파이낸스를 통해 실시간 환율 숫자를 직접 가져옵니다."""
    try:
        # 원/달러(USDKRW=X), 원/엔(JPYKRW=X)
        usd_krw = yf.Ticker("USDKRW=X").history(period='1d')['Close'].iloc[-1]
        jpy_krw = yf.Ticker("JPYKRW=X").history(period='1d')['Close'].iloc[-1]
        return round(usd_krw, 2), round(jpy_krw, 2)
    except Exception as e:
        print(f"환율 수치 수집 에러: {e}")
        return "정보 없음", "정보 없음"

def get_naver_exchange_news():
    """네이버 API를 통해 환율 분석 뉴스를 수집합니다."""
    queries = ["오늘 원달러 환율 시황 원인", "원엔 환율 변동 원인 분석"]
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
            print(f"네이버 API 에러 ({query}): {e}")
    return collected_news

def get_global_it_news():
    """NewsAPI를 통해 글로벌 IT/AI 뉴스를 수집합니다."""
    url = f"https://newsapi.org/v2/everything?q=AI+technology+trend&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        return res.json().get('articles', [])[:10]
    except Exception as e:
        print(f"NewsAPI 에러: {e}")
        return []

def get_memory():
    """어제 작성한 글 읽기"""
    try:
        list_of_files = glob.glob('_posts/*.md')
        if not list_of_files:
            return "첫 발행입니다."
        latest_file = sorted(list_of_files)[-1]
        with open(latest_file, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "기록 없음"

def run_news_agent():
    # 1. 모든 데이터 수집 (숫자 + 뉴스 + 기억)
    usd_val, jpy_val = get_realtime_exchange()
    exchange_news = get_naver_exchange_news()
    it_news = get_global_it_news()
    memory = get_memory()

    # 2. 모델 설정
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 3. 프롬프트 구성 (데이터 주입 강화)
    prompt = f"""
    너는 경제 애널리스트이자 IT 에디터야. 오늘 수집된 정확한 데이터들을 바탕으로 종합 리포트를 작성해. 
    데이터가 주어졌으므로 "데이터가 없다"는 말은 절대 하지마.

    [1. 실시간 환율 숫자]
    - 원/달러: {usd_val}원
    - 원/엔(100엔당): {jpy_val}원

    [2. 관련 환율 뉴스]
    {exchange_news}

    [3. 글로벌 IT 뉴스]
    {it_news}

    [4. 어제의 기록]
    {memory}

    [작성 가이드라인]
    - 섹션 1: 오늘의 환율 분석. 위 숫자({usd_val}, {jpy_val})를 반드시 명시하고, 뉴스 내용을 바탕으로 왜 환율이 이 수준인지 원인을 심층 분석해줘.
    - 섹션 2: 글로벌 IT TOP 3. 어제와 중복되지 않는 최신 AI 뉴스를 선정하고 요약해줘.
    - 섹션 3: 경제적 통찰. 환율 상황이 IT 업계나 한국 경제에 미칠 영향을 요약해줘.
    - 말투: 전문적이고 신뢰감 있는 한국어 (~입니다).
    - 형식: Jekyll 마크다운 본문만 (Front Matter 제외).
    """

    try:
        response = model.generate_content(prompt)
        
        # 한국 시간(KST) 설정
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        today_file = now.strftime("%Y-%m-%d")
        today_title = now.strftime("%Y/%m/%d")

        file_name = f"_posts/{today_file}-daily-briefing.md"
        os.makedirs('_posts', exist_ok=True)
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: single\n")
            f.write(f"title: \"{today_title} 경제 환율 & IT 뉴스\"\n")
            f.write(f"date: {today_file}\n")
            f.write(f"categories: [daily-news]\n")
            f.write(f"---\n\n")
            f.write(response.text)
            
        print(f"성공적으로 발행되었습니다: {file_name}")

    except Exception as e:
        print(f"에이전트 실행 에러: {e}")

if __name__ == "__main__":
    run_news_agent()
