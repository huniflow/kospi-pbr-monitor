import requests

def check_blocking():
    url = "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201010106"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"--- [진단 결과] ---")
        print(f"상태 코드: {response.status_code}")
        # 응답 내용이 너무 짧거나 '보안', 'Robot' 등의 단어가 있으면 차단입니다.
        print(f"응답 내용 앞부분: {response.text[:200]}") 
    except Exception as e:
        print(f"접속 자체가 안 됨: {e}")

check_blocking()
