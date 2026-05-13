#fetcher.py

import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from utils.config import Config
import time
import sys


def update_ticker_list():
    """
    시장 모드에 따라 상장 종목 리스트를 가져와 ticker_list.txt를 갱신합니다.
    [KR]: KOSPI, KOSDAQ 종목 (FinanceDataReader 활용)
    [US]: S&P500 또는 주요 나스닥 종목 (확장 가능)
    """
    mode = Config.MARKET_MODE
    ticker_file = Config.get("TICKER_FILE")
    
    print(f"--- 📋 [{mode}] 티커 리스트 업데이트 시작 ---")
    
    try:
        if mode == "KR":
            # 한국 상장 종목 전체 로드
            df_krx = fdr.StockListing('KRX')
            # 티커 포맷팅 (005930.KS 형태)
            df_krx['Ticker'] = df_krx.apply(
                lambda x: x['Code'] + ('.KS' if x['Market'] == 'KOSPI' else '.KQ'), axis=1
            )
            # '티커,종목명' 구조로 저장
            df_krx[['Ticker', 'Name']].to_csv(ticker_file, index=False, header=False, encoding='utf-8')
            
        elif mode == "US":
            # 미국 시장: S&P 500 리스트를 기본으로 사용 (FDR 활용)
            df_us = fdr.StockListing('S&P500')
            # 미국은 이름 매핑이 간단하므로 바로 저장
            df_us[['Symbol', 'Name']].to_csv(ticker_file, index=False, header=False, encoding='utf-8')

        print(f"✅ 티커 리스트 저장 완료: {ticker_file} (총 {len(df_krx if mode=='KR' else df_us)} 종목)")
        return True
        
    except Exception as e:
        print(f"❌ 티커 업데이트 실패: {e}")
        return False


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
    ticker_list.txt에 등록된 종목을 업데이트하며 진행률을 숫자로 표시합니다.
    """
    ticker_file = Config.get("TICKER_FILE")
    
    if not ticker_file.exists():
        print(f"❌ 티커 파일이 없습니다: {ticker_file}")
        return False

    with open(ticker_file, 'r', encoding='utf-8') as f:
        tickers = [line.strip().split(',')[0] for line in f if line.strip()]

    total = len(tickers)
    success_count = 0
    start_time = time.time()

    print(f"🚀 [{Config.MARKET_MODE}] 데이터 업데이트 시작")

    for i, ticker in enumerate(tickers, 1):
        # 데이터 수집 실행
        from core.fetcher import get_data_fetcher # 지연 임포트 방지
        success, msg = get_data_fetcher(ticker)
        if success:
            success_count += 1

        # 진행률 및 시간 계산
        percent = (i / total) * 100
        elapsed = time.time() - start_time
        eta = (elapsed / i) * (total - i) if i > 0 else 0
        
        # 출력 포맷: [50.1%] (1400/2800) | 성공: 1350 | 남은시간: 05:20
        # \r을 사용하여 한 줄에서 계속 갱신됩니다.
        sys.stdout.write(
            f"\r 진행률: {percent:>5.1f}% | ({i:>4}/{total:>4}) | "
            f"성공: {success_count:>4} | "
            f"ETA: {int(eta//60):02d}:{int(eta%60):02d} "
        )
        sys.stdout.flush()

    print(f"\n\n✅ 업데이트 완료! (최종 성공: {success_count} / 총 종목: {total})")
    return True

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