from pykrx import stock
from datetime import datetime, timedelta
import requests
import os
import time

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"메시지 전송 실패: {e}")

def get_safe_data(target_date):
    """라이브러리 내부 에러('지수명')를 방지하기 위한 안전 수집 함수"""
    try:
        # 데이터 수집 전 잠시 대기 (서버 부하 방지)
        time.sleep(2) 
        
        # 1. 펀더멘털 데이터 수집 시도
        df_f = stock.get_index_fundamental(target_date, target_date, "1001")
        
        # 2. 데이터가 정말 있는지, PBR 컬럼이 존재하는지 체크
        if df_f is not None and not df_f.empty and 'PBR' in df_f.columns:
            pbr = float(df_f['PBR'].iloc[-1])
            
            # 3. 지수 종가 데이터 수집
            df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")
            index = float(df_o['종가'].iloc[-1]) if (df_o is not None and not df_o.empty) else 0.0
            
            return index, pbr
    except Exception as e:
        # 내부 KeyError('지수명') 등이 발생하면 로그만 남기고 None 반환
        print(f"로그: {target_date} 조회 시 건너뜀 (사유: {e})")
    return None, None

try:
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    current_index, current_pbr = get_safe_data(today_str)
    
    date_label = "오늘"

    # 오늘 데이터가 0이거나 에러가 나면 최근 7일간 역추적
    if current_pbr is None or current_pbr == 0:
        for i in range(1, 8):
            check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            prev_index, prev_pbr = get_safe_data(check_date)
            
            if prev_pbr is not None and prev_pbr > 0:
                current_index, current_pbr = prev_index, prev_pbr
                date_label = f"최근({check_date[4:6]}/{check_date[6:8]})"
                break

    if current_pbr and current_pbr > 0:
        # 소수점 둘째 자리 포맷팅
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {date_label}\n"
        message += f"📉 지표: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다."
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "❌ 시스템 알림: 현재 KRX 서버 응답이 원활하지 않아 데이터를 가져올 수 없습니다. 나중에 다시 시도해 주세요."

    send_message(message)

except Exception as e:
    send_message(f"❌ 최종 실행 오류 발생\n({str(e)})")
