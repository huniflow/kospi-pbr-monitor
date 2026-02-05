import requests
import pandas as pd
import os
from datetime import datetime

# 1. 환경 변수 로드 (GitHub Secrets에서 관리)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
KOSIS_API_URL = os.environ.get('KOSIS_API_URL')

def send_message(text):
    """텔레그램 메시지 전송 (미리보기 비활성화)"""
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}&disable_web_page_preview=true"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"텔레그램 전송 에러: {e}")

def get_pbr_data():
    """KOSIS API 데이터 수집 및 정제"""
    if not KOSIS_API_URL:
        return "❌ 에러: GitHub Secrets에 KOSIS_API_URL이 설정되지 않았습니다.", None
    
    try:
        response = requests.get(KOSIS_API_URL, timeout=15)
        if response.status_code != 200:
            return f"❌ API 호출 실패 (Status: {response.status_code})", None
            
        json_data = response.json()
        df = pd.DataFrame(json_data)
        
        # 'KOSPI' 또는 '코스피' 항목 필터링 (방어로직)
        df_kospi = df[df['C1_NM'].isin(['KOSPI', '코스피'])].copy()
        if df_kospi.empty:
            return "❌ 데이터 내 KOSPI 항목을 찾을 수 없습니다.", None
            
        # 데이터 정제: 숫자 변환 및 날짜 형식 변환
        df_kospi['DT'] = pd.to_numeric(df_kospi['DT'], errors='coerce')
        df_kospi['PRD_DE'] = pd.to_datetime(df_kospi['PRD_DE'], format='%Y%m', errors='coerce')
        
        return None, df_kospi.dropna(subset=['DT']).sort_values('PRD_DE')

    except Exception as e:
        return f"❌ 시스템 오류: {str(e)}", None

try:
    print("--- PBR 시계열 분석 리포트 생성 시작 ---")
    
    # 데이터 가져오기
    error_msg, df = get_pbr_data()
    
    if error_msg:
        print(error_msg)
        send_message(error_msg)
    else:
        # 최근 5개월 추출 (최신순 정렬)
        recent_df = df.tail(5).iloc[::-1]
        
        # 메시지 구성
        message = f"📢 [투자 비서] KOSPI PBR 추이 리포트\n"
        message += f"────────────────\n"
        message += " 월별   |  PBR  |  투자 구간\n"
        message += "───────|───────|────────\n"
        
        for _, row in recent_df.iterrows():
            month = row['PRD_DE'].strftime('%y.%m')
            pbr = row['DT']
            
            # 투자 구간 판단 로직 (0.8 / 1.3)
            if pbr <= 0.8:
                zone = "🔥 적극매수"
            elif pbr > 1.3:
                zone = "⚠️ 위험매도"
            else:
                zone = "✅ 중립관망"
                
            message += f"{month}  |  {pbr:.2f}  |  {zone}\n"
            
        message += f"────────────────\n"
        message += f"💡 기준: 0.8이하(매수) / 1.3이상(매도)\n"
        message += f"────────────────\n"
        
        # 직관적인 당일 확인 링크
        message += f"🔍 [당일 KOSPI PBR 확인] (로그인 필요)\n"
        message += f"https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201"

        send_message(message)
        print("✅ 리포트 발송 성공")

except Exception as e:
    print(f"❌ 실행 오류: {e}")
