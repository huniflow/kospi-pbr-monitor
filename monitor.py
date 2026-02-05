from pykrx import stock
from datetime import datetime
import requests
import os

# 1. 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 실패: {e}")

try:
    # 오늘 날짜 확인 (YYYYMMDD 형식)
    today = datetime.now().strftime("%Y%m%d")
    
    # 1. KOSPI 지수 종가 가져오기
    # 1028은 코스피 지수의 고유 코드입니다.
    df_index = stock.get_index_price_indicator(today, today, "1028")
    
    # 2. KOSPI 지수 PBR 가져오기
    df_fundamental = stock.get_index_fundamental(today, today, "1028")

    if not df_fundamental.empty:
        current_pbr = float(df_fundamental['PBR'].iloc[-1])
        current_index = float(df_index['종가'].iloc[-1])

        # 3. 메시지 구성
        message = f"📢 KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_index:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr}\n"
        message += f"────────────────\n"

        # 후니님의 투자 원칙 반영
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 리스크 관리가 필요합니다."
        else:
            message += "⚖️ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "⏳ 현재 KRX에서 오늘의 지수 지표를 산출 중입니다. 잠시 후 다시 시도해 주세요."

    send_message(message)

except Exception as e:
    send_message(f"❌ 데이터 수집 중 오류 발생\n({str(e)})")
