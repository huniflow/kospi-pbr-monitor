import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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

def get_kospi_pbr():
    """네이버 금융에서 코스피 PBR을 직접 파싱 (GitHub 환경에서 가장 안정적)"""
    url = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 네이버 금융의 PBR 위치를 찾아냅니다.
        pbr_text = soup.find('td', {'id': 'pbr'}).get_text()
        return float(pbr_text)
    except Exception as e:
        print(f"PBR 파싱 실패: {e}")
        return None

try:
    # 1. 코스피 지수 가져오기 (FinanceDataReader 사용)
    df = fdr.DataReader('KS11')
    current_index = float(df['Close'].iloc[-1])
    
    # 2. 코스피 PBR 가져오기 (네이버 크롤링)
    current_pbr = get_kospi_pbr()

    if current_pbr is not None:
        # 3. 메시지 구성
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_index:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr:.2f}\n" # 소수점 둘째 자리
        message += f"────────────────\n"

        # 투자 원칙 적용: 0.8 이하 매수 / 1.3 초과 매도
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다. 비중 확대를 검토하세요!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달! 수익 실현 및 리스크 관리가 필요합니다."
        else:
            message += "✅ [중립/관망] 정상 범위 내에 있습니다."
    else:
        message = "❌ 시스템 알림: PBR 데이터를 수집할 수 없습니다. 네이버 금융 페이지 구조를 확인해주세요."

    send_message(message)

except Exception as e:
    send_message(f"❌ 실행 오류 발생: {str(e)}")
