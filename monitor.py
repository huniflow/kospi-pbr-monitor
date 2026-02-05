import requests
import pandas as pd
import os

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
KOSIS_API_URL = os.environ.get('KOSIS_API_URL')

def send_message(text):
    """MarkdownV2를 사용하여 고정 폭 글꼴 적용"""
    if TOKEN and CHAT_ID:
        # 마크다운을 사용하기 위해 parse_mode 추가
        url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TOKEN}/sendMessage"
        params = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown", # 마크다운 모드 활성화
            "disable_web_page_preview": True
        }
        try:
            requests.get(url, params=params, timeout=10)
        except Exception as e:
            print(f"전송 에러: {e}")

# ... (get_pbr_data 함수는 이전과 동일) ...

try:
    error_msg, df = get_pbr_data()
    
    if error_msg:
        send_message(error_msg)
    else:
        recent_df = df.tail(5).iloc[::-1]
        
        # 1. 상단 텍스트
        message = "📢 *[투자 비서] KOSPI PBR 리포트*\n\n"
        
        # 2. 표 시작 (백틱 3개로 감싸서 고정 폭 글꼴 적용)
        table_content = " 월별  |  PBR  |  투자구간\n"
        table_content += "-------|-------|---------\n"
        
        for _, row in recent_df.iterrows():
            month = row['PRD_DE'].strftime('%y.%m')
            pbr = row['DT']
            
            if pbr <= 0.8:
                zone = "🔥적극매수"
            elif pbr > 1.3:
                zone = "⚠️위험매도"
            else:
                zone = "✅중립관망"
            
            # f-string 정렬 (:<6 은 6칸 왼쪽 정렬, :>5.2f는 5칸 오른쪽 정렬)
            table_content += f"{month:<5} | {pbr:>5.2f} | {zone}\n"
        
        # 메시지에 코드 블록 형태로 삽입
        message += f"```\n{table_content}```\n"
        
        # 3. 하단 정보
        message += "💡 *기준: 0.8이하(매수) / 1.3이상(매도)*\n"
        message += "────────────────\n"
        message += "🔍 [당일 KOSPI PBR 확인]\n"
        message += "[https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201](https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201)"

        send_message(message)
        print("✅ 정렬된 리포트 발송 성공")

except Exception as e:
    print(f"❌ 오류: {e}")
