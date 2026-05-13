#fetcher.py

import os
import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from utils.config import Config

def get_data_fetcher(ticker):
    """
    시장 모드에 따라 적절한 데이터 수집 함수를 실행하고 저장합니다.
    """
    mode = Config.MARKET_MODE
    # Config에서 경로를 가져오고, 없으면 자동 생성
    save_dir = Config.get_path("DATA_DIR")
    save_path = save_dir / f"{ticker}_{Config.get('INTERVAL')}.csv"
    
    try:
        if mode == "KR":
            # 한국 시장: FinanceDataReader 사용 (일봉 기준)
            # 종료일은 오늘+1일로 설정하여 오늘 데이터 누락 방지
            end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d') # 2년치
            
            df = fdr.DataReader(ticker.split('.')[0], start=start_date, end=end_date)
            
        elif mode == "US":
            # 미국 시장: yfinance 사용 (4시간봉 등 정밀 설정 가능)
            ytick = yf.Ticker(ticker)
            df = ytick.history(period="2y", interval=Config.get("INTERVAL"))
            
        if df is None or df.empty:
            raise ValueError(f"데이터가 비어있습니다. (Ticker: {ticker})")

        # 데이터 저장 (Index는 Date)
        df.to_csv(save_path)
        return True, f"{ticker} 저장 완료"

    except Exception as e:
        # 에러 발생 시 상세 원인 반환
        error_msg = f"❌ [{ticker}] 수집 실패: {str(e)}"
        return False, error_msg

def update_all_tickers():
    """
    ticker_list.txt에 등록된 모든 종목을 업데이트합니다.
    """
    ticker_file = Config.get("TICKER_FILE")
    
    if not os.path.exists(ticker_file):
        return False, f"티커 파일이 없습니다: {ticker_file}"

    # 티커 파일 파싱 (티커,종목명 구조 대응)
    tickers = []
    with open(ticker_file, 'r', encoding='utf-8') as f:
        for line in f:
            if ',' in line:
                tickers.append(line.strip().split(',')[0])
            elif line.strip():
                tickers.append(line.strip())

    success_count = 0
    for t in tickers:
        success, msg = get_data_fetcher(t)
        if success:
            success_count += 1
        print(msg)
        
    return True, f"총 {len(tickers)}개 중 {success_count}개 업데이트 완료"

# --- [테스트 코드] ---
if __name__ == "__main__":
    # 1. 환경 변수 강제 설정 테스트 (필요시 주석 해제)
    # os.environ["MARKET_MODE"] = "KR" 
    
    print(f"현재 시장 모드: {Config.MARKET_MODE}")
    print(f"저장 경로: {Config.get('DATA_DIR')}")
    
    # 샘플 티커 테스트 (KR: 삼성전자, US: AAPL)
    test_ticker = "005930.KS" if Config.MARKET_MODE == "KR" else "AAPL"
    
    print(f"--- {test_ticker} 데이터 수집 테스트 시작 ---")
    success, result = get_data_fetcher(test_ticker)
    print(result)