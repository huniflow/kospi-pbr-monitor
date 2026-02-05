import FinanceDataReader as fdr
import requests
import os

# 환경 변수 로드 (Security 강화)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_alert(pbr, index):
    if pbr <= 0.8:
        status = "🚨 [적극 매수] 저평가 구간입니다!"
    elif pbr >= 1.3:
        status = "⚠️ [위험/매도] 고점 진입, 리스크 관리가 필요합니다."
    else:
        status = "✅ [관망] 정상 범위 내에 있습니다."
    
    msg = f"KOSPI: {index}\nPBR: {pbr}\n결과: {status}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")

# KRX 데이터 추출
df = fdr.StockListing('KRX-MARKTDATA')
kospi = df[df['Name'] == 'KOSPI']
send_alert(float(kospi['PBR'].values[0]), float(kospi['ClosingPrice'].values[0]))