import requests
import pandas as pd
import os

# 1. 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
KOSIS_API_URL = os.environ.get('KOSIS_API_URL')

def send_message(text):
    """Markdown 모드를 사용하여 고정 폭 글꼴 적용"""
    if TOKEN and CHAT_ID:
        url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TOKEN}/sendMessage"
        params = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            requests.get(url, params=params, timeout=10)
        except Exception as e:
            print(f"전송 에러: {e}")

def get_pbr_data():
    """KOSIS API 데이터 수집 및 정제"""
    if not KOSIS_API_URL:
        return "❌ 에러: KOSIS_API_URL 설정 확인 필요", None
    try:
        response = requests.get(KOSIS_API_URL, timeout=15)
        df = pd.DataFrame(response.json())
        df_kospi = df[df['C1_NM'].isin(['KOSPI', '코스피'])].copy()
        df_kospi['DT'] = pd.to_numeric(df_kospi['DT'], errors='coerce')
        df_kospi['PRD_DE'] = pd.to_datetime(df_kospi['PRD_DE'], format='%Y%m', errors='coerce')
        return None, df_kospi.dropna(subset=['DT']).sort_values('PRD_DE')
    except Exception as e:
        return f"❌ 시스템 오류: {str(e)}", None

try:
    error_msg, df = get_pbr_data()
    
    if error_msg:
        send_message(error_msg)
    else:
        # 최근 5개월 최신순
        recent_df = df.tail(5).iloc[::-1]
        
        # 메시지 헤더 (볼드체 적용)
        message = "📢 *[투자 비서] KOSPI PBR 리포트*\n\n"
        
        # 💡 표 전체를 고정 폭 코드 블록으로 묶기
        table = "월별  | PBR  | 판단\n"
        table += "------|------|------\n"
        
        for _, row in recent_df.iterrows():
            month = row['PRD_DE'].strftime('%y.%m')
            pbr = row['DT']
            
            # 후니님의 0.8/1.3 기준 적용
            if pbr <= 0.8:
                zone = "🔥매수"
            elif pbr > 1.3:
                zone = "⚠️위험"
            else:
                zone = "✅중립"
            
            # 간격 최적화 (PBR은 소수점 2자리)
            table += f"{month} | {pbr:>4.2f} | {zone}\n"
        
        # 표 완성
        message += f"```\n{table}```\n"
        
        # 하단 정보 및 직관적인 링크
        message += "💡 *기준: 0.8이하(매수) / 1.3이상(매도)*\n"
        message += "────────────────\n"
        message += "🔍 *[당일 KOSPI PBR 확인]* (로그인 필요)\n"
        message += "[https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201](https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201)"

        send_message(message)
        print("✅ 정렬 리포트 발송 완료")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
