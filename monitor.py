import FinanceDataReader as fdr
import requests
import os

# 1. 환경 변수 로드 (GitHub Secrets 연동)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        requests.get(url)

# 2. 실시간 데이터 수집 및 분석
try:
    # KRX 전체 종목/지수 리스트 수집
    df_krx = fdr.StockListing('KRX')
    
    # 코스피(KOSPI) 행 데이터만 추출
    kospi_row = df_krx[df_krx['Name'] == 'KOSPI']
    
    # 실시간 지수 및 PBR 값 추출
    current_index = float(kospi_row['ClosingPrice'].values[0])
    current_pbr = float(kospi_row['PBR'].values[0])

    # 3. 투자 원칙(PBR 0.8 / 1.3)에 따른 메시지 구성
    message = f"📢 [KOSPI PBR 비서] 실시간 KOSPI 브리핑\n"
    message += f"────────────────\n"
    message += f"📉 현재 지수: {current_index:,.2f}\n"
    message += f"📊 현재 PBR: {current_pbr}\n"
    message += f"────────────────\n"

    # 후니님의 매수/매도 규칙 적용
    if current_pbr <= 0.8:
        message += "🔥 [적극 매수] 시장이 매우 저렴합니다. 비중 확대를 검토하세요!"
    elif current_pbr > 1.3:
        message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
    else:
        message += "⚖️ [중립/관망] 정상 범위 내에 있습니다. 시장 상황을 지켜보세요."

    send_message(message)

except Exception as e:
    # 에러 발생 시 텔레그램으로 즉시 보고 (TPO의 위기 대응)
    send_message(f"❌ 모니터링 시스템 오류 발생: {str(e)}")
