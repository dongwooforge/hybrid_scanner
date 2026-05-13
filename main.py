from core.fetcher import update_ticker_list, update_all_tickers
from core.scanner import scan_tickers

def run_pipeline():
    update_ticker_list()  # 1. 리스트 갱신
    update_all_tickers()   # 2. 데이터 수집
    signals = scan_tickers() # 3. 시그널 스캔
    # 4. 결과 리포트 출력 또는 전송
run_pipeline()