import requests
import pandas as pd
import os
from datetime import datetime

# 1. 환경 변수 설정 (GitHub Secrets에서 로드)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
KOSIS_API_URL = os.environ.get('KOSIS_API_URL')

def send_message(text):
    """텔레그램 메시지 전송 (미리보기 방지 적용)"""
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}&disable_web_page_preview=true"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")

def get_pbr_data():
    """보안이 강화된 데이터 수집 및 방어 로직"""
    if not KOSIS_API_URL:
        print("에러: KOSIS_API_URL 환경 변수가 설정되지 않았습니다.")
        return None
    
    try:
        response = requests.get(KOSIS_API_URL, timeout=15)
        response.raise_for_status()
        
        # 데이터 존재 여부 확인
        if not response.text.strip():
            return None
            
        json_data = response.json()
        if not json_data or not isinstance(json_data, list):
            return None
            
        df = pd.DataFrame(json_data)
        
        # 필수 컬럼 존재 여부 체크 및 KOSPI 필터링
        if 'C1_NM' not in df.columns or 'DT' not in df.columns:
            return None
            
        df_kospi = df[df['C1_NM'] == 'KOSPI'].copy()
        
        # 데이터 타입 정제 (오류 값 제외)
        df_kospi['DT'] = pd.to_numeric(df_kospi['DT'], errors='coerce')
        df_kospi['PRD_DE'] = pd.to_datetime(df_kospi['PRD_DE'], format='%Y%m', errors='coerce')
        
        return df_kospi.dropna(subset=['DT']).sort_values('PRD_DE')

    except Exception as e:
        print(f"데이터 처리 중 오류: {e}")
        return None

try:
    print("--- 12개월 변동 분석 및 리포트 생성 시작 ---")
    
    # 데이터 확보
    df = get_pbr_data()
    
    # 검증 URL 설정
    krx_verify_url = "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201"

    if df is not None and not df.empty:
        # 주요 통계치 산출
        current_pbr = df['DT'].iloc[-1]
        last_month = df['PRD_DE'].iloc[-1].strftime('%Y년 %m월')
        high_12m = df['DT'].max()
        low_12m = df['DT'].min()
        
        # 메시지 구성
        message = f"📢 [후니의 투자 비서] PBR 분석 리포트\n"
        message += f"────────────────\n"
        message += f"📅 최근 기준일: {last_month}\n"
        message += f"📊 KOSPI PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"
        message += f"📈 12M 최고: {high_12m:.2f}\n"
        message += f"📉 12M 최저: {low_12m:.2f}\n"
        message += f"────────────────\n"

        # 투자 원칙 적용 (0.8 / 1.3 기준)
        if current_pbr <= 0.8:
            message += "🔥 [상태: 적극 매수]\n역사적 저평가 구간입니다! 기회를 잡으세요.\n"
        elif current_pbr > 1.3:
            message += "⚠️ [상태: 위험/매도]\n고평가 구간입니다. 리스크 관리가 필요합니다.\n"
        else:
            message += "✅ [상태: 관망/중립]\n시장이 정상 범위 내에 있습니다.\n"
        
        message += f"────────────────\n"
        # 직관적인 검증 링크 안내
        message += f"🔍 [당일 KOSPI PBR 확인] (로그인 필요)\n"
        message += f"{krx_verify_url}"

        send_message(message)
        print(f"✅ 발송 성공 (PBR: {current_pbr})")
    else:
        send_message("❌ [시스템 알림] 데이터 수집에 실패했습니다. GitHub Secrets의 API URL 설정을 확인해주세요.")

except Exception as e:
    print(f"❌ 실행 중 치명적 오류: {e}")
