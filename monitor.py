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
        requests.get(url)

# 2. 데이터 수집 및 예외 처리
try:
    # KOSPI 지수 데이터를 직접 호출 (KS11은 코스피 지수의 심볼입니다)
    df_kospi = fdr.DataReader('KS11')
    
    # KRX 전체 상장사 데이터를 통해 PBR 지표 추출
    df_listing = fdr.StockListing('KRX')
    
    if df_kospi.empty or df_listing.empty:
        raise ValueError("데이터 원천으로부터 정보를 불러오지 못했습니다.")

    # 최신 종가 및 PBR 추출
    current_index = float(df_kospi['Close'].iloc[-1])
    
    # KRX 리스트에서 KOSPI 지표 행 찾기 (이름이 'KOSPI' 또는 '코스피'일 수 있음)
    kospi_info = df_listing[df_listing['Name'].str.contains('KOSPI|코스피', na=False)]
    
    if not kospi_info.empty and not pd.isna(kospi_info['PBR'].values[0]):
        current_pbr = float(kospi_info['PBR'].values[0])
        
        # 3. 메시지 구성
        message = f"📢 KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_index:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr}\n"
        message += f"────────────────\n"

        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 매우 저렴합니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "⚖️ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = f"⏳ 지수는 {current_index:,.2f}이나, 현재 PBR 데이터를 산출할 수 없는 시간대입니다."

    send_message(message)

except Exception as e:
    send_message(f"❌ 시스템 알림: 데이터 확인 필요\n({str(e)})")
