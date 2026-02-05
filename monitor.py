from pykrx import stock
from datetime import datetime
import requests
import os
import pandas as pd

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            # 네트워크 타임아웃 10초 설정
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 실패: {e}")

try:
    # 오늘 날짜 확인 (YYYYMMDD)
    today = datetime.now().strftime("%Y%m%d")
    
    # 1. KOSPI 지수 종가 데이터 가져오기 (티커 '1001')
    df_ohlcv = stock.get_index_ohlcv_by_date(today, today, "1001")
    
    # 2. KOSPI 지수 펀더멘털(PBR) 데이터 가져오기
    df_fundamental = stock.get_index_fundamental(today, today, "1001")

    if not df_fundamental.empty and not df_ohlcv.empty:
        current_index = float(df_ohlcv['종가'].iloc[-1])
        current_pbr = float(df_fundamental['PBR'].iloc[-1])
        
        # PBR 데이터 미확정(0.0)에 대한 방어 로직
        if current_pbr == 0:
            raise ValueError("현재 PBR 데이터가 아직 확정되지 않았습니다 (0.0으로 조회됨).")

        # 3. 메시지 구성
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_index:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr:.2f}\n" # 소수점 둘째 자리까지 표시
        message += f"────────────────\n"

        # 투자 원칙 적용 (PBR 0.8 이하 매수 / 1.3 초과 매도)
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "⏳ 현재 KRX에서 오늘의 지수 지표를 산출 중입니다. 잠시 후 다시 시도해 주세요."

    send_message(message)

except Exception as e:
    send_message(f"❌ 시스템 알림: 데이터 확인 필요\n({str(e)})")
