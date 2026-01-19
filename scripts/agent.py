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

def get_market_data():
    """야후 파이낸스에서 환율 및 주요 증시 지수를 가져옵니다."""
    try:
        # 원/달러, 원/엔, S&P500(^GSPC), 나스닥(^IXIC)
        usd_krw = yf.Ticker("USDKRW=X").history(period='1d')['Close'].iloc[-1]
        jpy_krw = yf.Ticker("JPYKRW=X").history(period='1d')['Close'].iloc[-1]
        sp500 = yf.Ticker("^GSPC").history(period='1d')['Close'].iloc[-1]
        nasdaq = yf.Ticker("^IXIC").history(period='1d')['Close'].iloc[-1]
        
        return {
            "usd": round(usd_krw, 2),
            "jpy": round(jpy_krw, 2),
            "sp500": round(sp500, 2),
            "nasdaq": round(nasdaq, 2)
        }
    except Exception as e:
        print(f"시장 지표 수집 에러: {e}")
        return {"usd": "정보 없음", "jpy": "정보 없음", "sp500": "정보 없음", "nasdaq": "정보 없음"}

def get_naver_exchange_news():
    """네이버 API를 통해 국내 환율 분석 뉴스를 수집합니다."""
    queries = ["오늘 원달러 환율 시황 원인", "원엔 환율 전망 분석"]
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
        except:
            pass
    return collected_news

def get_bigtech_news():
    """NewsAPI를 통해 미국 빅테크 및 증시 관련 뉴스를 수집합니다."""
    # 키워드를 빅테크와 미국 증시(S&P 500, NASDAQ) 중심으로 변경
    query = "(Apple OR Microsoft OR NVIDIA OR Google OR Amazon OR Meta OR Tesla) AND (stock market OR NASDAQ OR S&P 500)"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        return res.json().get('articles', [])[:10]
    except:
        return []

def get_memory():
    """어제 작성한 글 읽기"""
    try:
        list_of_files = glob.glob('_posts/*.md')
        if not list_of_files: return "첫 발행입니다."
        latest_file = sorted(list_of_files)[-1]
        with open(latest_file, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "기록 없음"

def run_news_agent():
    # 1. 데이터 수집
    market = get_market_data()
    exchange_news = get_naver_exchange_news()
    bigtech_news = get_bigtech_news()
    memory = get_memory()

    # 2. 모델 설정 (Gemini 2.5 Flash)
    model = genai.GenerativeModel('gemini-2.5-flash')


    # 3. 프롬프트 구성 (증시와 환율의 연결 분석 강조)
    prompt = f"""
    너는 글로벌 금융 및 IT 전략가야. 아래 데이터를 바탕으로 오늘의 경제 브리핑을 작성해줘.

    [시장 지표]
    - 원/달러: {market['usd']}원 / 원/엔(100엔): {market['jpy']}원
    - S&P 500: {market['sp500']} / 나스닥: {market['nasdaq']}

    [뉴스 데이터]
    - 국내 환율 시황: {exchange_news}
    - 미국 빅테크 및 증시 소식: {bigtech_news}

    [어제의 기록]
    {memory}

    [작성 가이드라인]
    1. **환율 & 증시 리포트**: 오늘 환율 수치와 미국 증시 지수({market['sp500']}, {market['nasdaq']})를 먼저 언급하고, 상관관계를 분석해줘. (예: 기술주 강세가 달러 가치에 미친 영향 등)
    2. **빅테크 뉴스 분석**: 수집된 빅테크 뉴스 중 증시에 큰 영향을 준 3가지를 골라 요약하고, 이것이 한국 IT 기업(삼성전자, SK하이닉스 등)에 줄 시사점을 적어줘.
    3. **연속성**: 어제 내용과 중복되지 않게 하되, 흐름이 이어진다면 언급해줘.
    4. **말투**: 전문적이고 통찰력 있는 한국어 (~입니다).

    [출력 형식]
    1. **시각적 요소**: 적절한 이모지(📊, 💹, 🚀 등)를 사용해 가독성을 높여줘.
    2. **서식**: 핵심 수치는 **굵게(Bold)** 표시하고, 주요 섹션은 마크다운 헤더(###)를 사용해줘.
    3. **표 활용**: 오늘의 시장 지표(환율, 증시)를 마크다운 표(Table) 형식으로 정리해서 최상단에 보여줘.
    4. **내용**: 
       - **[Part 1. 마켓 대시보드]**: 지표 정리 및 짧은 분석.
       - **[Part 2. 빅테크 & 증시 이슈]**: 가장 중요한 뉴스 3가지를 번호 매겨 요약.
       - **[Part 3. 인사이트]**: 한국 시장에 주는 시사점.
    5. **제한**: 블로그 포스팅용 본문 내용만 출력해. "알겠습니다" 같은 서론이나 끝인사는 절대 포함하지 마.
    
    [출력 예시]
    ### 📊 오늘의 시장 지표
    | 지표 | 현재가 | 상태 |
    | :--- | :--- | :--- |
    | 원/달러 | 1,3xx원 | ... |
    ... (이런 식으로 작성)
    """

    try:
        response = model.generate_content(prompt)
        
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        today_file = now.strftime("%Y-%m-%d")
        today_title = now.strftime("%Y/%m/%d")

        file_name = f"_posts/{today_file}-market-tech-briefing.md"
        os.makedirs('_posts', exist_ok=True)
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: single\n")
            f.write(f"title: \"{today_title} 증시 지표 & 빅테크 뉴스 브리핑\"\n")
            f.write(f"date: {today_file}\n")
            f.write(f"categories: [daily-news]\n")
            f.write(f"---\n\n")
            f.write(response.text)
            
        print(f"발행 완료: {file_name}")
    except Exception as e:
        print(f"에러: {e}")

if __name__ == "__main__":
    run_news_agent()
