from pykrx import stock
from datetime import datetime, timedelta
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
            print(f"전송 실패: {e}")

def get_pbr_data(target_date):
    """특정 날짜의 데이터를 안전하게 가져오는 함수"""
    try:
        # 코스피 지수의 가장 표준적인 코드 '1001'을 사용합니다.
        df_f = stock.get_index_fundamental(target_date, target_date, "1001")
        df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")
        
        # '지수명' 에러 방지를 위해 데이터프레임이 비어있는지 먼저 체크합니다.
        if df_f is not None and not df_f.empty and 'PBR' in df_f.columns:
            pbr = float(df_f['PBR'].iloc[-1])
            index = float(df_o['종가'].iloc[-1]) if not df_o.empty else 0.0
            return index, pbr
    except Exception as e:
        # TPO의 관점에서 상세 에러 로그를 남겨 디버깅을 돕습니다.
        print(f"로그: {target_date} 조회 중 오류 발생 (무시하고 진행): {e}")
    return None, None

try:
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    current_index, current_pbr = get_pbr_data(today_str)
    
    date_label = "오늘"

    # 오늘 데이터가 없거나 0.0이면 최근 7일간의 데이터를 역추적합니다.
    if current_pbr is None or current_pbr == 0:
        for i in range(1, 8):
            check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            prev_index, prev_pbr = get_pbr_data(check_date)
            
            if prev_pbr is not None and prev_pbr > 0:
                current_index, current_pbr = prev_index, prev_pbr
                date_label = f"최근({check_date[4:6]}/{check_date[6:8]})"
                break

    if current_pbr and current_pbr > 0:
        # 소수점 둘째 자리까지 포맷팅
        message = f"📢 KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {date_label}\n"
        message += f"📉 지표: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # PBR 0.8 이하 매수 / 1.3 초과 매도 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "❌ 시스템 알림: 유효한 데이터를 찾을 수 없습니다. (거래소 점검 혹은 라이브러리 이슈)"

    send_message(message)

except Exception as e:
    send_message(f"❌ 최종 실행 오류: {str(e)}")
