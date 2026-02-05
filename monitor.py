from pykrx import stock
from datetime import datetime, timedelta
import requests
import os

# 1. 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    """텔레그램 메시지 전송 함수"""
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 실패: {e}")

def get_valid_data(target_date):
    """특정 날짜의 유효한 데이터를 가져오는 함수"""
    try:
        # 코스피 지수(1001)의 펀더멘털(PBR 등) 및 종가 데이터 수집
        df_f = stock.get_index_fundamental(target_date, target_date, "1001")
        df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")
        
        if df_f is not None and not df_f.empty:
            pbr = float(df_f['PBR'].iloc[-1])
            # PBR이 0이면 아직 데이터가 확정되지 않은 것으로 간주
            if pbr > 0:
                idx = float(df_o['종가'].iloc[-1]) if not df_o.empty else 0.0
                return idx, pbr
    except:
        pass
    return None, None

try:
    now = datetime.now()
    current_index, current_pbr = None, None
    final_date = ""

    print("최근 영업일 데이터 탐색을 시작합니다.")

    # 어제(1일 전)부터 시작해서 최대 10일 전까지 유효한 영업일 데이터를 역추적
    for i in range(1, 11):
        check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
        idx, pbr = get_valid_data(check_date)
        
        if pbr is not None:
            current_index, current_pbr = idx, pbr
            final_date = check_date
            break

    if current_pbr:
        # 2. 메시지 구성 (소수점 둘째 자리 및 천 단위 콤마 적용)
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {final_date[:4]}-{final_date[4:6]}-{final_date[6:]}\n"
        message += f"📉 지수: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # 후니님의 0.8/1.3 투자 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 시장이 정상 범위 내에 있습니다."

        send_message(message)
        print(f"성공: {final_date} 데이터 기반 리포트 발송 완료")
    else:
        send_message("❌ 시스템 알림: 최근 10일 내 유효한 영업일 데이터를 찾을 수 없습니다. 거래소 상태를 확인해주세요.")

except Exception as e:
    send_message(f"❌ 최종 실행 오류 발생: {str(e)}")
