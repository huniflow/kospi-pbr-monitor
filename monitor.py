import FinanceDataReader as fdr
import requests
import os
import pandas as pd

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 에러: {e}")

try:
    # 1. 지수 데이터 수집
    df_kospi = fdr.DataReader('KS11')
    current_index = float(df_kospi['Close'].iloc[-1])
    
    # 2. KRX 전체 리스트 수집
    df_listing = fdr.StockListing('KRX')
    
    # [수정] 더 유연한 이름 검색 (contains 사용 및 대소문자 무시)
    # 'KOSPI', '코스피', 'KOSPI 지수' 등을 모두 포괄합니다.
    kospi_info = df_listing[df_listing['Name'].str.contains('KOSPI|코스피', case=False, na=False)]
    
    # PBR 데이터 추출 시도
    pbr_value = None
    if not kospi_info.empty:
        # 검색된 결과 중 가장 상단 데이터의 PBR 확인
        pbr_value = kospi_info['PBR'].values[0]

    # 3. 데이터 판정 및 메시지 발송
    if pbr_value and not pd.isna(pbr_value):
        current_pbr = float(pbr_value)
        message = f"📢 KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_index:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr}\n"
        message += f"────────────────\n"

        # 후니님의 투자 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다."
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 고점 신호! 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        # 데이터가 없는 경우 원인 분석 메시지
        message = f"📉 지수: {current_index:,.2f}\n"
        message += "⏳ 현재 KRX에서 오늘의 PBR 수치를 산출 중입니다.\n(보통 16:30 이후 데이터가 확정됩니다.)"

    send_message(message)

except Exception as e:
    send_message(f"❌ 데이터 수집 중 확인 필요\n({str(e)})")
