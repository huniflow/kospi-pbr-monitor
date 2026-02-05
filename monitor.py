import requests
import pandas as pd
import os

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
KOSIS_API_URL = os.environ.get('KOSIS_API_URL')

def send_message(text):
    """Markdown 모드를 사용하여 표 정렬 유지"""
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
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
        # 'KOSPI' 또는 '코스피' 대응
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
        # 최근 5개월 최신순 정렬
        recent_df = df.tail(5).iloc[::-1]
        
        message = "📢 *[투자 비서] KOSPI PBR 리포트*\n\n"
        
        # 💡 표 전체를 코드 블록(```)으로 묶어 고정 폭 글꼴 적용
        table = "월별  | PBR  | 판단\n"
        table += "------|------|------\n"
        
        for _, row in recent_df.iterrows():
            month = row['PRD_DE'].strftime('%y.%m')
            pbr = row['DT']
            
            # 투자 구간 판단
            if pbr <= 0.8:
                zone = "🔥매수"
            elif pbr > 1.3:
                zone = "⚠️위험"
            else:
                zone = "✅중립"
            
            # f-string 정렬로 칸 맞춤
            table += f"{month} | {pbr:>4.2f} | {zone}\n"
        
        message += f"```\n{table}```\n"
        message += "💡 *기준: 0.8이하(매수) / 1.3이상(매도)*\n"
        message += "────────────────\n"
        message += "🔍 *[당일 KOSPI PBR 확인]* (로그인 필요)\n"
        message += "[https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201](https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201)"

        send_message(message)
        print("✅ 정렬 리포트 발송 완료")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
