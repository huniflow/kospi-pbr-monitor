import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
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
            print(f"텔레그램 실패: {e}")

def get_pbr_from_naver_fundamental():
    """가장 깔끔한 '지수 펀더멘털' 페이지에서 PBR 추출"""
    # [TPO 전략] 시세 페이지 대신 펀더멘털 전용 페이지 사용
    url = "https://finance.naver.com/sise/sise_index_fundamental.naver?code=KOSPI"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 테이블 내의 모든 td를 돌며 'PBR' 단어를 찾습니다.
        target_td = soup.find('td', string='PBR')
        if not target_td:
            # 혹시 텍스트가 바로 안 잡힐 경우 전체 검색
            for td in soup.find_all('td'):
                if 'PBR' in td.get_text():
                    target_td = td
                    break
        
        if target_td:
            # 'PBR' 글자가 있는 td 바로 다음 td에 숫자가 있습니다.
            pbr_val = target_td.find_next_sibling('td').get_text().strip()
            return float(pbr_val)
            
    except Exception as e:
        print(f"로그: 펀더멘털 페이지 파싱 실패 -> {e}")
    return None

try:
    print("--- 펀더멘털 전용 페이지 탐색 시작 ---")
    
    # 지수 종가는 FinanceDataReader로 안전하게 확보
    df = fdr.DataReader('KS11')
    current_idx = float(df['Close'].iloc[-1])
    
    # PBR은 네이버 전용 페이지에서 추출
    current_pbr = get_pbr_from_naver_fundamental()

    if current_pbr:
        # 소수점 둘째 자리 포맷팅 적용
        message = f"📢 [후니의 비서] KOSPI 리포트\n"
        message += f"────────────────\n"
        message += f"📉 지수 종가: {current_idx:,.2f}\n"
        message += f"📊 시장 PBR: {current_pbr:.2f}\n"
        message += f"────────────────\n"

        # 0.8/1.3 투자 원칙 적용
        if current_pbr <= 0.8:
            message += "🔥 [적극 매수] 역사적 저평가 구간입니다!"
        elif current_pbr > 1.3:
            message += "⚠️ [위험/매도] 리스크 관리가 시급합니다!"
        else:
            message += "✅ [중립/관망] 시장이 정상 범위 내에 있습니다."
        
        send_message(message)
        print(f"✅ 리포트 발송 성공! (PBR: {current_pbr})")
    else:
        # 실패 시 로그를 상세히 남겨 다음 대응을 준비합니다.
        error_msg = "❌ 에러: 네이버 펀더멘털 페이지에서도 PBR을 찾지 못했습니다."
        print(error_msg)
        send_message(error_msg)

except Exception as e:
    send_message(f"❌ 실행 중 치명적 오류: {str(e)}")
