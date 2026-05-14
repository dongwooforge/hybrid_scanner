"""
================================================================================
[ 정밀 전략 테스터 : Single Ticker Deep Analyzer ]
1. 분석 대상: 개별 종목 (티커 기반)
2. 핵심 지표: 
   - MAE (Maximum Adverse Excursion): 진입 후 겪는 최대 하락폭 (고통 지수)
   - MFE (Maximum Favorable Excursion): 진입 후 달성한 최대 상승폭 (환희 지수)
   - Holding 기간별 효율성 분석 (5일, 20일, 60일)
================================================================================
"""
import pandas as pd
import numpy as np
from core.scanner import load_strategy_logic
from utils.config import Config

# RSI 함수 (my_private_logic.txt 내에서 호출 가능하도록 환경 주입용)
def get_rsi(series, period):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    # alpha=1/period 설정으로 파인스크립트 rma 방식과 유사하게 구현
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def run_deep_test(ticker):
    # 1. 데이터 로드 (D: 일봉 데이터, 파일명 규격 반영)
    data_dir = Config.get_path("DATA_DIR")
    # 파일 탐색기 확인 결과: {ticker}_1d.csv 규격 [현장 확인 반영]
    file_path = data_dir / f"{ticker}_1d.csv"
    
    if not file_path.exists():
        print(f"❌ 경로 오류: {file_path}")
        print(f"❌ {ticker} 데이터를 찾을 수 없습니다. 파일명과 raw_data 폴더를 확인해주세요.")
        return

    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    
    # 2. 전략 로직 주입 (exec 환경 구성)
    logic_code = load_strategy_logic()
    # local_vars에 필요한 유틸리티 함수들을 담아 전달
    local_vars = {'df': df, 'get_rsi': get_rsi, 'pd': pd, 'np': np}
    exec(logic_code, {}, local_vars)
    df = local_vars['df']

    # 3. 시그널 발생 지점 추출
    signals = df[df['Signal'] == True].copy()
    if signals.empty:
        print(f"📭 {ticker}: 분석 기간 내 발생한 B-Signal(바닥 탈출)이 없습니다.")
        return

    trade_log = []
    
    # 4. 개별 진입건별 전수 조사 (최대 60거래일 추적)
    for entry_date in signals.index:
        # 진입 시점 이후의 데이터 슬라이싱
        idx = df.index.get_loc(entry_date)
        after_entry = df.iloc[idx+1 : idx+61] 
        
        if len(after_entry) < 5: continue # 데이터 부족 시 제외
        
        entry_price = df.loc[entry_date, 'Close']
        max_high = after_entry['High'].max()
        min_low = after_entry['Low'].min()
        
        # 보유 기간별 종가 수익률 계산
        holding_rets = {
            '5d': (after_entry['Close'].iloc[min(4, len(after_entry)-1)] - entry_price) / entry_price * 100,
            '20d': (after_entry['Close'].iloc[min(19, len(after_entry)-1)] - entry_price) / entry_price * 100,
            '60d': (after_entry['Close'].iloc[-1] - entry_price) / entry_price * 100
        }
        
        trade_log.append({
            'date': entry_date,
            'mfe': (max_high - entry_price) / entry_price * 100, # 최대 반등
            'mae': (min_low - entry_price) / entry_price * 100,  # 최대 낙폭
            **holding_rets
        })

    # 5. 분석 결과 리포트 출력
    res = pd.DataFrame(trade_log)
    print(f"\n--- 🔬 [{ticker}] 정밀 전략 분석 보고서 ---")
    print(f"✅ 분석 기간: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"✅ 총 진입 횟수: {len(res)}회")
    print("-" * 55)
    print("📊 [심리/변동성 지표]")
    print(f" - 평균 최대 상승(MFE): {res['mfe'].mean():.2f}%")
    print(f" - 평균 최대 하락(MAE): {res['mae'].mean():.2f}% (진입 후 견뎌야 할 고통)")
    print(f" - 최악의 순간 낙폭: {res['mae'].min():.2f}%")
    print("-" * 55)
    print("⏳ [보유 기간별 평균 수익률]")
    print(f" - 5일(단타): {res['5d'].mean():.2f}%")
    print(f" - 20일(스윙): {res['20d'].mean():.2f}%")
    print(f" - 60일(중기): {res['60d'].mean():.2f}%")
    
    # 성과 기반 매매 스타일 추천
    best_p = res[['5d', '20d', '60d']].mean().idxmax()
    style = "단타" if best_p == '5d' else "스윙" if best_p == '20d' else "장기보유"
    
    print("\n💡 [동우님을 위한 투자 가이드]")
    print(f" -> 이 종목은 **[{best_p}]** 보유 시 평균 성과가 가장 좋으며, **[{style}]** 스타일에 적합합니다.")
    print(f" -> 진입 후 평균 {abs(res['mae'].mean()):.1f}% 정도의 마이너스는 견뎌야 수익을 얻을 수 있습니다.")

# 실행: 삼성전자 정밀 분석
if __name__ == "__main__":
    run_deep_test("066575.KS")