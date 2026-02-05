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
    try:
        # [보정] 티커 번호 1001 대신 'KOSPI' 명칭을 사용하는 것이 더 안정적일 때가 있습니다.
        # 지수 종가 (OHLCV)
        df_ohlcv = stock.get_index_ohlcv_by_date(target_date, target_date, "KOSPI")
        # 지수 펀더멘털 (PBR 등)
        df_fundamental = stock.get_index_fundamental(target_date, target_date, "KOSPI")
        
        # 데이터가 있고, 필요한 컬럼이 존재하는지 확인
        if not df_fundamental.empty and 'PBR' in df_fundamental.columns:
            pbr = float(df_fundamental['PBR'].iloc[-1])
            index = float(df_ohlcv['종가'].iloc[-1]) if not df_ohlcv.empty else 0.0
            return index, pbr
    except Exception as e:
        print(f"로그: {target_date} 데이터 추출 중 상세 에러 발생: {e}")
    return None, None

try:
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    current_index, current_pbr = get_pbr_data(today_str)
    
    date_label = "오늘"

    # 오늘 데이터가 없거나 0.0이면 최근 영업일 역추적 (최대 7일)
    if current_pbr is None or current_pbr == 0:
        for i in range(1, 8):
            check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            prev_index, prev_pbr = get_pbr_data(check_date)
            
            if prev_pbr is not None and prev_pbr > 0:
                current_index, current_pbr = prev_index, prev_pbr
                date_label = f"최근({check_date[4:6]}/{check_date[6:8]})"
                break

    if current_pbr and current_pbr > 0:
        # 소수점 둘째 자리 포맷팅 적용
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {date_label}\n"
        message += f"📉 지표: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # 후니님의 투자 원칙 (PBR 0.8 이하 매수 / 1.3 초과 매도)
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "❌ 시스템 알림: 유효한 PBR 데이터를 찾을 수 없습니다. (거래소 점검 중일 수 있습니다.)"

    send_message(message)

except Exception as e:
    # 에러 메시지를 구체적으로 전송하여 디버깅 용이성 확보
    send_message(f"❌ 오류 발생: {str(e)}")
