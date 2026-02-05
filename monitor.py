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
            print(f"전송 실패: {e}")

def get_safe_data(target_date):
    """라이브러리 내부 에러를 방지하고 상세 로그를 남기는 함수"""
    try:
        # 서버 부하를 줄이기 위해 3초 대기
        time.sleep(3) 
        
        # 1. 펀더멘털 데이터 수집 (KOSPI=1001)
        df_f = stock.get_index_fundamental(target_date, target_date, "1001")
        
        # 데이터가 비어있는지 로깅 (GitHub Actions 로그에서 확인 가능)
        if df_f is None or df_f.empty:
            print(f"로그: {target_date} PBR 데이터가 비어있습니다.")
            return None, None
            
        if 'PBR' not in df_f.columns:
            print(f"로그: {target_date} 데이터에 'PBR' 컬럼이 없습니다.")
            return None, None

        pbr = float(df_f['PBR'].iloc[-1])
        
        # 2. 지수 종가 데이터 수집
        df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")
        index = float(df_o['종가'].iloc[-1]) if (df_o is not None and not df_o.empty) else 0.0
        
        return index, pbr
    except Exception as e:
        print(f"로그: {target_date} 처리 중 에러 발생: {e}")
    return None, None

try:
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    print(f"시스템 가동: {today_str} 데이터 수집 시도...")
    
    current_index, current_pbr = get_safe_data(today_str)
    date_label = "오늘"

    # 오늘 데이터가 없으면 최근 10일까지 끈질기게 추적
    if current_pbr is None or current_pbr == 0:
        print("오늘 데이터 수집 불가. 과거 데이터 탐색(Backtracking) 시작...")
        for i in range(1, 11):
            check_date = (now - timedelta(days=i)).strftime("%Y%m%d")
            prev_index, prev_pbr = get_safe_data(check_date)
            
            if prev_pbr is not None and prev_pbr > 0:
                current_index, current_pbr = prev_index, prev_pbr
                date_label = f"최근({check_date[4:6]}/{check_date[6:8]})"
                print(f"성공: {check_date} 데이터를 찾았습니다.")
                break

    if current_pbr and current_pbr > 0:
        # 소수점 둘째 자리 포맷팅 적용
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {date_label}\n"
        message += f"📉 지표: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # 후니님의 0.8/1.3 투자 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "❌ 시스템 알림: 거래소 서버 응답 지연으로 데이터를 가져올 수 없습니다. 잠시 후 수동 실행(workflow_dispatch)을 권장합니다."

    send_message(message)

except Exception as e:
    send_message(f"❌ 최종 실행 오류: {str(e)}")
