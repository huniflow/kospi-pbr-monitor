import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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

def get_naver_pbr():
    """네이버 금융에서 코스피 PBR을 직접 가져옴 (GitHub 환경 최적화)"""
    url = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 네이버 금융의 PBR 데이터 ID인 'pbr'을 찾습니다.
        pbr_val = soup.find('td', {'id': 'pbr'}).get_text()
        return float(pbr_val)
    except:
        return None

try:
    # 2. 지수 데이터 (FinanceDataReader는 Yahoo/Naver를 써서 안정적임)
    df = fdr.DataReader('KS11')
    current_idx = float(df['Close'].iloc[-1])
    
    # 3. PBR 데이터 (네이버 직접 파싱)
    current_pbr = get_naver_pbr()

    if current_pbr:
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 현재 지수: {current_idx:,.2f}\n"
        message += f"📊 현재 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 시장이 저평가 상태입니다."
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 역사적 고점 도달!"
        else:
            message += "✅ [중립/관망] 정상 범위 구간"
        
        send_message(message)
        print(f"성공: 리포트 발송 완료 (PBR: {current_pbr})")
    else:
        print("실패: PBR 데이터를 가져오지 못했습니다.")

except Exception as e:
    send_message(f"❌ 최종 오류 발생: {str(e)}")
