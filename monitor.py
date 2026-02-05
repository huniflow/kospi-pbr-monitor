from pykrx import stock
from datetime import datetime, timedelta
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
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 실패: {e}")

def get_pbr_data(target_date):
    """특정 날짜의 코스피 지수와 PBR을 가져오는 함수"""
    # 1001은 KOSPI 지수 티커 번호
    df_ohlcv = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")
    df_fundamental = stock.get_index_fundamental(target_date, target_date, "1001")
    
    if not df_fundamental.empty and not df_ohlcv.empty:
        pbr = float(df_fundamental['PBR'].iloc[-1])
        index = float(df_ohlcv['종가'].iloc[-1])
        return index, pbr
    return None, None

try:
    # 1. 오늘 데이터 시도
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    current_index, current_pbr = get_pbr_data(today_str)
    
    date_label = "오늘"

    # 2. 오늘 데이터가 없거나 0.0이면 어제(혹은 최근 영업일) 데이터를 찾음 (최대 5일 전까지 역추적)
    if current_pbr is None or current_pbr == 0:
        print("오늘 데이터가 확정되지 않아 최근 영업일 데이터를 탐색합니다.")
        for i in range(1, 6):
            check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            prev_index, prev_pbr = get_pbr_data(check_date)
            
            if prev_pbr is not None and prev_pbr > 0:
                current_index, current_pbr = prev_index, prev_pbr
                date_label = f"최근({check_date[4:6]}/{check_date[6:8]})"
                break

    # 3. 데이터가 최종적으로 확보되었는지 확인 후 메시지 구성
    if current_pbr and current_pbr > 0:
        message = f"📢 KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {date_label}\n"
        message += f"📉 지표: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n" # 소수점 둘째 자리 유지
        message += f"────────────────\n"

        # 투자 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다."
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 리스크 관리가 필요합니다."
        else:
            message += "⚖️ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "❌ 시스템 알림: 최근 영업일의 PBR 데이터를 모두 찾을 수 없습니다. 거래소 공시를 확인해주세요."

    send_message(message)

except Exception as e:
    send_message(f"❌ 데이터 수집 중 오류 발생\n({str(e)})")
