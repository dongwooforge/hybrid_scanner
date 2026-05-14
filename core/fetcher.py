#fetcher.py

import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from utils.config import Config
import time
import sys
import pandas as pd


"""
================================================================================
[ MODULE : core/fetcher.py ]
- 역할: 온라인(Yahoo/FDR) 주가 데이터를 수집하여 로컬 storage에 증분 저장(Incremental Update)
- 연계: utils/config(경로/설정), storage/(데이터 배출)
================================================================================
1. INPUT (입력)
   - Ticker: str (예: 'AAPL', '005930.KS')
   - 기존 파일 존재 여부: storage/{MARKET}/{TICKER}.csv 확인

2. OUTPUT (출력)
   - File Path: storage/{MARKET_MODE}/{TICKER}_{INTERVAL}.csv
   - Process: 신규 데이터와 기존 데이터 병합(Merge) 후 중복 제거(Drop Duplicates)

3. 연계 작용 (Data Flow)
   - [IN]  Local Storage: 기존에 저장된 데이터의 마지막 날짜(Last Date) 확인
   - [FETCH] Online: (Last Date - 1일)부터 오늘까지의 최신 데이터만 요청
   - [OUT] Local Storage: 병합된 최종 데이터를 다시 동일 경로에 덮어쓰기
================================================================================
"""


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
    증분 업데이트(Incremental Update) 방식으로 데이터를 수집합니다.
    기존 데이터가 있으면 마지막 날짜부터 수집하여 합칩니다.
    """
    mode = Config.MARKET_MODE
    save_dir = Config.get_path("DATA_DIR")
    save_path = save_dir / f"{ticker}_{Config.get('INTERVAL')}.csv"
    
    # 1. 기존 데이터 확인 및 시작 날짜 설정
    start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d') # 기본 2년
    existing_df = None
    
    if save_path.exists():
        try:
            existing_df = pd.read_csv(save_path, index_col=0, parse_dates=True)
            if not existing_df.empty:
                # 마지막 날짜로부터 1일 전부터 수집 (장중 데이터 갱신을 위함)
                last_date = existing_df.index[-1]
                start_date = (last_date - timedelta(days=1)).strftime('%Y-%m-%d')
        except Exception as e:
            print(f"⚠️ {ticker} 기존 파일 로드 실패(새로 수집): {e}")

    try:
        end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        new_df = None

        # 2. 신규 데이터 수집
        if mode == "KR":
            new_df = fdr.DataReader(ticker.split('.')[0], start=start_date, end=end_date)
        elif mode == "US":
            ytick = yf.Ticker(ticker)
            new_df = ytick.history(start=start_date, end=end_date, interval=Config.get("INTERVAL"))
            
        if new_df is None or new_df.empty:
            if existing_df is not None: # 신규 데이터가 없어도 기존 데이터가 있으면 유지
                return True, f"{ticker} (신규 데이터 없음)"
            raise ValueError("수집된 데이터가 없습니다.")

        # 3. 데이터 병합 및 중복 제거
        if existing_df is not None:
            # 합치기: 기존 데이터 + 신규 데이터
            combined_df = pd.concat([existing_df, new_df])
            # 중복 제거: Index(날짜) 기준으로 마지막에 들어온 데이터(신규)를 우선함
            combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
            combined_df.sort_index(inplace=True)
            final_df = combined_df
        else:
            final_df = new_df

        # 4. 저장
        final_df.to_csv(save_path)
        return True, f"{ticker} 업데이트 완료"

    except Exception as e:
        return False, f"❌ [{ticker}] 수집 실패: {str(e)}"



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
    
    
    
    
    
    
