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
    # 테스트를 위해 어제 날짜(20260204)로 강제 고정
    target_date = "20260204"
    print(f"테스트 시작: {target_date} 데이터를 강제로 호출합니다.")

    # 2. 데이터 수집 시도 (KOSPI 지수 코드: 1001)
    df_f = stock.get_index_fundamental(target_date, target_date, "1001")
    df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")

    if df_f is not None and not df_f.empty:
        current_pbr = float(df_f['PBR'].iloc[-1])
        current_index = float(df_o['종가'].iloc[-1]) if not df_o.empty else 0.0

        # 3. 메시지 구성 (소수점 둘째 자리 포맷 적용)
        message = f"📊 [KOSPI 테스트 리포트]\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {target_date}\n"
        message += f"📉 지수: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # 투자 판단 기준 (0.8 / 1.3)
        if current_pbr <= 0.8:
            message += "🔥 시장 저평가 구간입니다."
        elif current_pbr > 1.3:
            message += "⚠️ 시장 고평가 구간입니다."
        else:
            message += "✅ 정상 범위 내에 있습니다."

        send_message(message)
        print("성공: 텔레그램 메시지를 발송했습니다.")
    else:
        print(f"실패: {target_date}에 해당하는 데이터를 찾을 수 없습니다.")

except Exception as e:
    # 상세 에러 메시지 출력 (깃허브 로그 확인용)
