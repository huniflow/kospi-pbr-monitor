from pykrx import stock
from datetime import datetime, timedelta
import requests
import os

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

def get_pbr_safe(target_date):
    """지명 에러를 방지하기 위해 예외 처리가 강화된 데이터 수집 함수"""
    try:
        # 1001: 코스피 지수 고유 코드
        df_f = stock.get_index_fundamental(target_date, target_date, "1001")
        df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")
        
        if df_f is not None and not df_f.empty and 'PBR' in df_f.columns:
            pbr = float(df_f['PBR'].iloc[-1])
            idx = float(df_o['종가'].iloc[-1]) if not df_o.empty else 0.0
            if pbr > 0: # PBR이 0보다 커야 유효한 데이터로 간주
                return idx, pbr
    except:
        pass
    return None, None

try:
    now = datetime.now()
    
    # 주말(토:5, 일:6)이면 실행하지 않고 종료
    if now.weekday() >= 5:
        print("오늘은 주말입니다. 리포트를 발송하지 않습니다.")
    else:
        print("평일 리포트 생성을 시작합니다.")
        current_index, current_pbr = None, None
        display_date = ""

        # 전날부터 시작해서 최대 10일 전까지 가장 최근 영업일 데이터를 탐색
        for i in range(1, 11):
            check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            idx, pbr = get_pbr_safe(check_date)
            
            if pbr is not None:
                current_index, current_pbr = idx, pbr
                display_date = f"{check_date[4:6]}/{check_date[6:8]}"
                break

        if current_pbr:
            message = f"📢 [후니의 비서] KOSPI 리포트\n"
            message += f"────────────────\n"
            message += f"📅 기준일: {display_date} (최근 영업일)\n"
            message += f"📉 지수: {current_index:,.2f}\n"
            message += f"📊 PBR: {current_pbr:.2f}\n" # 소수점 둘째 자리 적용
            message += f"────────────────\n"

            # 투자 원칙 적용
            if current_pbr <= 0.8:
                message += "🔥 [적극 매수] 시장이 저평가 상태입니다."
            elif current_pbr > 1.3:
                message += "⚠️ [위험/매도] 역사적 고점 도달! 주의하세요."
            else:
                message += "✅ [중립/관망] 정상 범위 내에 있습니다."
            
            send_message(message)
        else:
            print("최근 영업일 데이터를 찾을 수 없습니다. (거래소 점검 등)")

except Exception as e:
    print(f"실행 중 오류 발생: {e}")
