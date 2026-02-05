import FinanceDataReader as fdr
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 1. 환경 변수 안전 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_message(text):
    """텔레그램 알림 전송"""
    if TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={text}"
        try:
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"전송 실패: {e}")

def get_pbr_from_naver():
    """네이버 금융 펀더멘털 페이지에서 PBR 추출 (가장 안정적)"""
    url = "https://finance.naver.com/sise/sise_index_fundamental.naver?code=KOSPI"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 'PBR' 글자 바로 옆 칸의 숫자를 찾는 정밀 타겟팅
        target_td = soup.find('td', string='PBR')
        if not target_td:
            for td in soup.find_all('td'):
                if 'PBR' in td.get_text():
                    target_td = td
                    break
        
        if target_td:
            pbr_text = target_td.find_next_sibling('td').get_text().strip()
            return float(pbr_text)
    except Exception as e:
        print(f"PBR 파싱 오류: {e}")
    return None

try:
    now = datetime.now()
    # 주말(토, 일) 필터링
    if now.weekday() >= 5:
        print("오늘은 휴장일(주말)이므로 리포트를 발송하지 않습니다.")
    else:
        print(f"--- {now.strftime('%Y-%m-%d')} 리포트 생성 시작 ---")
        
        # 지수 종가 가져오기
        df = fdr.DataReader('KS11')
        current_idx = float(df['Close'].iloc[-1])
        
        # PBR 데이터 가져오기
        current_pbr = get_pbr_from_naver()

        if current_pbr:
            # 메시지 포맷팅 (소수점 둘째 자리)
            message = f"📢 [후니의 비서] KOSPI 리포트\n"
            message += f"────────────────\n"
            message += f"📉 지수 종가: {current_idx:,.2f}\n"
            message += f"📊 시장 PBR: {current_pbr:.2f}\n"
            message += f"────────────────\n"

            # 0.8 / 1.3 투자 원칙 적용
            if current_pbr <= 0.8:
                message += "🔥 [적극 매수] 역사적 저평가 구간입니다!"
            elif current_pbr > 1.3:
                message += "⚠️ [위험/매도] 리스크 관리가 시급합니다!"
            else:
                message += "✅ [중립/관망] 정상 범위 구간입니다."
            
            send_message(message)
            print(f"✅ 발송 성공 (PBR: {current_pbr})")
        else:
            print("❌ 실패: PBR 데이터를 찾지 못했습니다.")

except Exception as e:
    send_message(f"❌ 실행 중 치명적 오류: {str(e)}")
