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

# 2. 데이터 수집 및 예외 처리 로직
try:
    # KRX 전체 시장 데이터 로드
    df_krx = fdr.StockListing('KRX')
    
    # 코스피(KOSPI) 행 추출
    kospi_row = df_krx[df_krx['Name'] == 'KOSPI']
    
    if kospi_row.empty:
        raise ValueError("KOSPI 데이터를 찾을 수 없습니다.")

    # 데이터 추출 (NaN 값 대비)
    raw_index = kospi_row['ClosingPrice'].values[0]
    raw_pbr = kospi_row['PBR'].values[0]

    # 데이터 존재 여부 확인 (TPO의 꼼꼼한 예외 처리)
    if pd.isna(raw_index) or pd.isna(raw_pbr):
        # 데이터가 비어있을 경우 (장외 시간 또는 거래소 업데이트 지연)
        message = "⏳ 현재 실시간 데이터를 불러올 수 없습니다.\n(장외 시간이거나 거래소 데이터 업데이트 중입니다.)"
    else:
        current_index = float(raw_index)
        current_pbr = float(raw_pbr)

        # 3. 투자 원칙에 따른 메시지 구성
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

    send_message(message)

except Exception as e:
    # 예기치 못한 에러 발생 시 알림 (디버깅용)
    send_message(f"❌ 시스템 알림: 데이터 처리 중 확인이 필요합니다.\n({str(e)})")
