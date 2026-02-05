import requests
import pandas as pd
import os
from datetime import datetime

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
KOSIS_API_URL = os.environ.get('KOSIS_API_URL')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}&disable_web_page_preview=true"
        requests.get(url, timeout=10)

def get_pbr_data():
    if not KOSIS_API_URL:
        return "❌ 에러: GitHub Secrets에 KOSIS_API_URL이 설정되지 않았습니다.", None
    
    try:
        response = requests.get(KOSIS_API_URL, timeout=15)
        
        # 🛡️ 디버깅 포인트 1: 응답 상태 코드 확인
        if response.status_code != 200:
            return f"❌ API 서버 응답 에러 (Status: {response.status_code})", None
            
        # 🛡️ 디버깅 포인트 2: 결과값이 비어있는지 확인
        raw_text = response.text.strip()
        if not raw_text:
            return "❌ API 응답이 비어있습니다. (URL을 다시 확인해주세요)", None
            
        json_data = response.json()
        
        # 🛡️ 디버깅 포인트 3: KOSIS 특유의 에러 메시지 처리
        if isinstance(json_data, dict) and "err" in str(json_data).lower():
            return f"❌ KOSIS API 내부 에러: {json_data}", None

        df = pd.DataFrame(json_data)
        
        # 🛡️ 디버깅 포인트 4: 데이터 필터링 확인
        if 'C1_NM' not in df.columns:
            return f"❌ 데이터 구조 오류: 'C1_NM' 컬럼이 없습니다. (받은 데이터: {raw_text[:100]}...)", None
            
        df_kospi = df[df['C1_NM'] == 'KOSPI'].copy()
        if df_kospi.empty:
            # 💡 팁: 'KOSPI'가 아니라 '코스피'로 들어올 수도 있습니다.
            df_kospi = df[df['C1_NM'] == '코스피'].copy()
            
        if df_kospi.empty:
            return "❌ KOSPI 항목을 찾을 수 없습니다. (C1_NM 값을 확인하세요)", None
            
        df_kospi['DT'] = pd.to_numeric(df_kospi['DT'], errors='coerce')
        df_kospi['PRD_DE'] = pd.to_datetime(df_kospi['PRD_DE'], format='%Y%m', errors='coerce')
        
        return None, df_kospi.dropna(subset=['DT']).sort_values('PRD_DE')

    except Exception as e:
        return f"❌ 시스템 오류: {str(e)}", None

try:
    error_msg, df = get_pbr_data()
    
    if error_msg:
        print(error_msg)
        send_message(error_msg) # 텔레그램으로도 에러 내용을 쏩니다.
    else:
        # 데이터가 정상일 경우 리포트 생성
        current_pbr = df['DT'].iloc[-1]
        last_month = df['PRD_DE'].iloc[-1].strftime('%Y년 %m월')
        high_12m = df['DT'].max()
        low_12m = df['DT'].min()
        
        message = f"📢 [후니의 투자 비서] PBR 리포트\n"
        message += f"────────────────\n"
        message += f"📅 최근 기준일: {last_month}\n"
        message += f"📊 KOSPI PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"
        message += f"📈 12M 최고: {high_12m:.2f}\n"
        message += f"📉 12M 최저: {low_12m:.2f}\n"
        message += f"────────────────\n"
        
        if current_pbr <= 0.8:
            message += "🔥 [상태: 적극 매수]\n"
        elif current_pbr > 1.3:
            message += "⚠️ [상태: 위험/매도]\n"
        else:
            message += "✅ [상태: 관망/중립]\n"
            
        message += f"────────────────\n"
        message += f"🔍 [당일 KOSPI PBR 확인] (로그인 필요)\n"
        message += f"https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201"

        send_message(message)
        print("✅ 리포트 발송 성공")

except Exception as e:
    print(f"❌ 실행 중 오류: {e}")
