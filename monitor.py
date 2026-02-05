import FinanceDataReader as fdr
import requests
import os
import pandas as pd

# 1. 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            # [고도화 1] 네트워크 타임아웃 설정 (10초)
            # 서버 응답이 지연될 경우 시스템이 무한정 대기하는 것을 방지한다.
            requests.get(url, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"메시지 전송 실패: {e}")

# 2. 데이터 수집 및 예외 처리
try:
    # KOSPI 지수 데이터를 직접 호출
    df_kospi = fdr.DataReader('KS11')
    
    # KRX 전체 상장사/지수 데이터 로드
    df_listing = fdr.StockListing('KRX')
    
    if df_kospi.empty or df_listing.empty:
        raise ValueError("데이터 원천으로부터 정보를 불러오지 못했습니다.")

    # 최신 종가 추출
    current_index = float(df_kospi['Close'].iloc[-1])
    
    # [고도화 2] 데이터 선별 로직 강화
    # 'KOSPI 200', 'KOSPI 중소형주' 등이 섞이지 않도록 정확히 'KOSPI' 명칭과 일치하는 행만 선별한다.
    kospi_info = df_listing[df_listing['Name'] == 'KOSPI']
    
    # 만약 정확한 매칭이 없다면 '코스피'로 재시도한다.
    if kospi_info.empty:
        kospi_info = df_listing[df_listing['Name'] == '코스피']
    
    if not kospi_info.empty and not pd.isna(kospi_info['PBR'].values[0]):
        current_pbr = float(kospi_info['PBR'].values[0])
        
        # 3. 메시지 구성 (사용자 정의 원칙 반영)
        message = f"📢 KOSPI 실시간 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_index:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr}\n"
        message += f"────────────────\n"

        # PBR 0.8 이하 매수, 1.3 초과 매도 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 매우 저렴합니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "⚖️ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = f"⏳ 지수는 {current_index:,.2f}이나, 현재 정확한 PBR 데이터를 찾을 수 없습니다."

    send_message(message)

except Exception as e:
    send_message(f"❌ 시스템 알림: 데이터 확인 필요\n({str(e)})")
