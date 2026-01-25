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
    """야후 파이낸스의 전일 종가 데이터를 직접 활용하여 변동폭을 가져옵니다."""
    tickers = {
        "usd": "USDKRW=X",
        "jpy": "JPYKRW=X",
        "sp500": "^GSPC",
        "nasdaq": "^IXIC"
    }
    results = {}
    try:
        for key, symbol in tickers.items():
            ticker = yf.Ticker(symbol)
            
            # 야후에서 제공하는 '전일 종가'와 '현재가' 가져오기
            # fast_info를 사용하면 info보다 훨씬 빠르게 데이터를 가져올 수 있습니다.
            fast_info = ticker.fast_info
            current_price = fast_info['last_price']
            prev_price = fast_info['previous_close']
            
            # 전일 대비 변동 계산 (야후 데이터 기준)
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
            
            # 시각적 아이콘 설정
            icon = "▲" if change > 0 else "▼" if change < 0 else "-"
            
            results[key] = {
                "current": round(current_price, 2),
                "prev": round(prev_price, 2), # Gemini가 아닌 야후가 알려준 전일가
                "diff": round(change, 2),
                "percent": round(change_percent, 2),
                "icon": icon
            }
        return results
    except Exception as e:
        print(f"시장 데이터 수집 에러: {e}")
        return None
        
def get_naver_exchange_news():
    """네이버 API를 통해 국내 환율 분석 뉴스를 수집합니다."""
    queries = ["원달러 환율 원인", "원엔 환율 원인"]
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
    """NewsAPI를 통해 미국 빅테크 및 S&P 500 시장 뉴스를 수집합니다."""
    # 빅테크 7대 기업 + S&P 500 지수 영향력이 큰 거시 경제 키워드 추가
    query = (
        "(Apple OR Microsoft OR NVIDIA OR Google OR Amazon OR Meta OR Tesla) "
        "OR (S&P 500 OR NASDAQ OR Federal Reserve OR inflation OR interest rates)"
    )
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        # 10개에서 15개로 늘려서 더 풍부한 정보를 AI에게 전달합니다.
        return res.json().get('articles', [])[:15]
    except:
        return []

def get_memory(target_category="daily-news"):
    """
    _posts 폴더의 md 파일들을 최신순으로 조회하여,
    설정된 target_category(기본값: daily-news)와 일치하는
    가장 최근 글의 내용을 반환합니다.
    """
    try:
        # 파일 목록 가져오기
        list_of_files = glob.glob('_posts/*.md')
        if not list_of_files: 
            return "첫 발행입니다."

        # 최신 파일이 먼저 오도록 역순 정렬 (매우 중요)
        sorted_files = sorted(list_of_files, reverse=True)

        for file_path in sorted_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 지킬 Front Matter 형식 확인
                    # categories: [daily-news] 또는 categories: daily-news 모두 체크
                    if f"categories: [{target_category}]" in content or \
                       f"categories: {target_category}" in content or \
                       f"category: {target_category}" in content:
                        print(f"🔍 이전 기록 발견: {file_path}")
                        return content
            except Exception as e:
                continue # 파일 읽기 에러나면 다음 파일로 넘어감
                    
        return f"'{target_category}' 카테고리의 이전 기록이 없습니다."
    except Exception as e:
        return f"메모리 읽기 실패: {str(e)}"

def run_news_agent():
    # 1. 데이터 수집
    market = get_market_data()
    exchange_news = get_naver_exchange_news()
    bigtech_news = get_bigtech_news()
    memory = get_memory("daily-news")

    # 2. 모델 설정 (Gemini 2.5 Flash)
    model = genai.GenerativeModel('gemini-2.5-flash')


    # 3. 프롬프트 구성 (증시와 환율의 연결 분석 강조)
    prompt = f"""
    너는 글로벌 금융 및 IT 전략가야. 아래 데이터를 바탕으로 오늘의 경제 브리핑을 작성해줘.

    [시장 지표 데이터 (전일 대비 포함)]
    - 원/달러: 현재 {market['usd']['current']}, 전일 {market['usd']['prev']} ({market['usd']['icon']} {market['usd']['diff']})
    - 원/엔(100엔): 현재 {market['jpy']['current']}, 전일 {market['jpy']['prev']} ({market['jpy']['icon']} {market['jpy']['diff']})
    - S&P 500: 현재 {market['sp500']['current']}, 전일 {market['sp500']['prev']} ({market['sp500']['icon']} {market['sp500']['diff']})
    - 나스닥: 현재 {market['nasdaq']['current']}, 전일 {market['nasdaq']['prev']} ({market['nasdaq']['icon']} {market['nasdaq']['diff']})

    [뉴스 및 기억]
    - 국내 환율 시황: {exchange_news}
    - 빅테크/증시 소식: {bigtech_news}
    - 어제 리포트 요약: {memory}

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
    | 지표 | 현재가 | 전일대비(변동폭) | 상태(아이콘)
    | :--- | :--- | :--- | :---
    | 원/달러 | 1,3xx원 | ... | ...
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
