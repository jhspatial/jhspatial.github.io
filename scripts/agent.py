import os
import requests
import glob
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)

def get_memory():
    """_posts 폴더에서 가장 최근 게시글의 내용을 읽어와 에이전트의 기억으로 반환합니다."""
    try:
        # _posts 폴더 내의 모든 .md 파일을 가져와 이름순으로 정렬
        list_of_files = glob.glob('_posts/*.md')
        if not list_of_files:
            return "이전에 작성한 게시글이 없습니다. 오늘이 첫 발행입니다."
        
        # 파일 이름순 정렬 시 가장 마지막 파일이 최신 날짜임
        latest_file = sorted(list_of_files)[-1]
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        print(f"기억 읽기 실패: {e}")
        return "이전 기록을 불러올 수 없습니다."

def run_news_agent():
    # 1. 에이전트의 '기억' 불러오기 (어제 쓴 글 확인)
    memory = get_memory()

    # 2. 뉴스 수집 (최신 AI 기술 관련 뉴스 10개)
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

    # 3. 모델 설정 (요청하신 최신 모델 적용)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # 4. 프롬프트 설정 (기억 데이터와 새로운 뉴스 주입)
    prompt = f"""
    너는 기술 전문 블로그 'IT 인사이트'를 운영하는 전문 에디터야. 
    너는 방금 전까지 어제자 블로그 포스팅을 마쳤고, 이제 오늘의 새로운 글을 쓸 차례야.
    아 그리고 it관련 학과 재학중인 사람의 개인 사이트에 포스팅하는 거야.

    [네가 어제 작성한 글 (기억)]
    {memory}

    [방금 수집된 오늘 뉴스 후보]
    {articles}

    [작성 미션]
    1. **중복 검토**: 위 [기억]에 포함된 뉴스 주제나 제목은 오늘 글에서 절대 다시 다루지 마. 완전히 새로운 소식을 선정해.
    2. **TOP 3 선정**: 후보 뉴스 중 IT관련 학계, 직무를 가지고 있는 사람들이 흥미로워할 소식 3가지를 엄선해줘.
    3. **내용 구성**: 
       - 📌 **핵심 요약**: 전문적인 톤으로 한문단 이내 요약.
       - 그리고 고등학생 수준의 영어로 요약하고 밑에 한국어 번역한 것도 넣어줄래
       - 💡 **전문가 견해**: 산업 전반에 미칠 영향이나 통찰을 한 문장으로 추가.
       - 🔗 **관련 링크**: [원문 읽기](URL) 형식으로 포함.
    4. **말투**: 독자에게 신뢰를 주는 전문적인 한국어 문체 (~입니다, ~합니다).

    [출력 포맷]
    - Jekyll 블로그용 마크다운 본문만 출력해 (Front Matter 제외).
    - 각 뉴스 섹션 사이에는 구분선(---)을 넣어줘.
    """
    
    try:
        # 콘텐츠 생성
        response = model.generate_content(prompt)
        
        # 5. 한국 시간(KST) 설정 및 날짜 추출
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst) 
        today_file = now.strftime("%Y-%m-%d")    
        today_title = now.strftime("%Y/%m/%d")   
        
        # 파일 저장 경로 (_posts 폴더 생성)
        file_name = f"_posts/{today_file}-daily-ai-news.md"
        os.makedirs('_posts', exist_ok=True)
        
        # 6. 최종 파일 쓰기
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"layout: single\n")
            f.write(f"title: \"{today_title} AI NEWS\"\n")
            f.write(f"date: {today_file}\n")
            f.write(f"categories: [daily-news]\n")
            f.write(f"---\n\n")
            f.write(response.text)
            
        print(f"성공적으로 발행되었습니다: {file_name} (KST 기준)")
        
    except Exception as e:
        print(f"에이전트 실행 에러: {e}")

if __name__ == "__main__":
    run_news_agent()
