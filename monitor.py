from pykrx import stock
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
    # 테스트를 위해 데이터가 확실한 어제 날짜(20260204) 고정
    target_date = "20260204"
    print(f"--- {target_date} 데이터 호출 테스트 시작 ---")

    # 2. 데이터 수집 (KOSPI 고유 코드 1001 사용)
    df_f = stock.get_index_fundamental(target_date, target_date, "1001")
    df_o = stock.get_index_ohlcv_by_date(target_date, target_date, "1001")

    if df_f is not None and not df_f.empty:
        current_pbr = float(df_f['PBR'].iloc[-1])
        current_index = float(df_o['종가'].iloc[-1]) if not df_o.empty else 0.0

        # 3. 메시지 구성 (소수점 둘째 자리 적용)
        message = f"📢 [KOSPI 테스트 리포트]\n"
        message += f"────────────────\n"
        message += f"📅 기준일: {target_date}\n"
        message += f"📉 지수: {current_index:,.2f}\n"
        message += f"📊 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # 후니님의 0.8/1.3 원칙 반영
        if current_pbr <= 0.8:
            message += "🔥 적극 매수 권장 구간입니다."
        elif current_pbr > 1.3:
            message += "⚠️ 리스크 관리 및 매도 검토 구간입니다."
        else:
            message += "✅ 시장이 정상 범위 내에 있습니다."

        send_message(message)
        print(f"성공: {target_date} 데이터 발송 완료 (PBR: {current_pbr:.2f})")
    else:
        print(f"데이터 없음: {target_date}의 데이터를 거래소에서 가져오지 못했습니다.")

except Exception as e:
    # 상세 에러 로그 출력
    error_log = f"❌ 시스템 오류 발생: {str(e)}"
    print(error_log)
    send_message(error_log)
