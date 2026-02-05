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
        # 메시지 미리보기 비활성화 (링크가 많아 화면을 가리는 것 방지)
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}&disable_web_page_preview=true"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 실패: {e}")

def get_etf_pbr(ticker="069500"):
    """KODEX 200 ETF의 PBR을 네이버에서 추출 (가장 안정적)"""
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        pbr_area = soup.find('em', id='_pbr')
        if pbr_area:
            return float(pbr_area.get_text())
    except:
        return None

try:
    # 데이터 수집 및 지수 확보
    df = fdr.DataReader('KS11')
    current_idx = float(df['Close'].iloc[-1])
    etf_pbr = get_etf_pbr()

    # KRX 공식 확인 주소
    krx_verify_url = "https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201"

    if etf_pbr:
        # 보정 로직 (ETF는 전체 시장보다 약 0.1 높음)
        estimated_kospi_pbr = round(etf_pbr - 0.1, 2)

        # 메시지 구성
        message = f"📢 [후니의 투자 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📈 KOSPI 지수: {current_idx:,.2f}\n"
        message += f"📊 KODEX 200 PBR: {etf_pbr:.2f}\n"
        message += f"🧐 예상 KOSPI PBR: {estimated_kospi_pbr:.2f}\n"
        message += f"────────────────\n"

        # 후니님의 0.8 / 1.3 투자 원칙 적용
        if estimated_kospi_pbr <= 0.8:
            message += "🔥 [상태: 적극 매수]\n시장이 역사적 저평가 구간입니다!"
        elif estimated_kospi_pbr > 1.3:
            message += "⚠️ [상태: 위험/매도]\n시장이 고평가되었습니다. 수익 실현을 검토하세요!"
        else:
            message += "✅ [상태: 관망/중립]\n시장이 정상 범위 내에 있습니다."
        
        message += f"\n────────────────\n"
        message += f"💡 [보정 기준 안내]\n"
        message += f"KODEX 200은 우량주 위주라 전체 시장보다 약 0.1 정도 높게 나옵니다. "
        message += f"이를 보정한 '예상 PBR'을 기준으로 판단합니다.\n\n"
        
        # 원천 데이터 확인 및 로그인 안내 추가
        message += f"🔐 KRX 원천 데이터 확인 (로그인 필요):\n"
        message += f"{krx_verify_url}"

        send_message(message)
        print(f"✅ 리포트 발송 완료 (Target: KRX Data Portal)")
    else:
        print("❌ 실패: 데이터를 수집하지 못했습니다.")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
