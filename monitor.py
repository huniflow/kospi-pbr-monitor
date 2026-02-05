import FinanceDataReader as fdr
import requests
import os

# 1. 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        requests.get(url)

# 2. 데이터 가져오기 (KRX 전체 종목 리스트 및 지수 정보)
try:
    # 'KRX'는 유가증권, 코스닥, 코넥스를 모두 포함합니다.
    df = fdr.StockListing('KRX')
    
    # 지수 정보를 직접 가져오는 함수로 대체 (더 확실한 방법)
    # 코스피(KOSPI)의 현재 지수와 PBR 데이터 추출
    # FinanceDataReader의 최신 규격에 맞춰 지수 데이터를 가져옵니다.
    kospi_index = fdr.DataReader('KS11') # KOSPI 지수
    current_index = float(kospi_index['Close'].iloc[-1])
    
    # PBR 데이터의 경우 StockListing에서 제공하는 값을 사용하거나 
    # 고정된 로직으로 계산이 필요할 수 있습니다. 
    # 여기서는 후니님의 차트 기반 분석 수치(1.35)를 예시로 로직을 구성합니다.
    # (참고: 실시간 PBR은 거래소 제공 데이터 스펙에 따라 달라질 수 있음)
    
    # 예시를 위해 최근 차트에서 확인된 PBR 1.35를 기준으로 조건문을 태웁니다.
    # 실제 운영 시에는 fdr에서 제공하는 지표 컬럼명을 확인하여 매칭하세요.
    current_pbr = 1.35 # 테스트를 위해 현재 차트 수치 반영
    
    message = f"현재 KOSPI 지수: {current_index:.2f}\n현재 예상 PBR: {current_pbr}\n\n"

    if current_pbr <= 0.8:
        message += "🚨 [적극 매수] PBR 0.8 이하! 저평가 구간입니다."
    elif current_pbr > 1.3:
        message += "⚠️ [관리/매도] PBR 1.3 초과! 역사적 고점 부근입니다."
    else:
        message += "✅ [관망/중립] 정상 범위 내에 있습니다."

    send_message(message)

except Exception as e:
    send_message(f"스크립트 실행 중 에러 발생: {str(e)}")
