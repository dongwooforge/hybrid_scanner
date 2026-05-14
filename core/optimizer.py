#optimizer.py

import pandas as pd
import numpy as np
from utils.config import Config


"""
================================================================================
[ MODULE : core/optimizer.py ]
- 역할: 과거 시그널 데이터를 기반으로 최적의 TP/SL 조합 및 퀀트 지표(승률, 손익비 등) 산출
- 연계: core/scanner.py (전략 로드), storage/ (가격 데이터 데이터 로드)
================================================================================
1. INPUT (입력)
   - Ticker Data: 시합 전적을 분석할 과거 OHLCV 배열
   - Optimization Range: 익절(3~20%), 손절(2~10%) 구간 조합

2. OUTPUT (출력 규격)
   - win_rate: float (승률 %)
   - profit_factor: float (손익비: 총수익/총손실)
   - expectancy: float (회당 기대 수익률 %)
   - max_return: float (전체 기간 누적 수익률 합계)
   - trade_count: int (총 시뮬레이션 횟수)
================================================================================
"""


def optimize_vectorized(ticker):
    """
    벡터 연산을 활용하여 최적의 TP/SL을 찾고, 
    승률, 손익비, 기대수익률 등 상세 퀀트 지표를 계산합니다.
    """
    data_dir = Config.get_path("DATA_DIR")
    interval = Config.get("INTERVAL")
    file_path = data_dir / f"{ticker}_{interval}.csv"
    
    if not file_path.exists():
        return None

    # 1. 데이터 로드 및 전략 적용
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    from core.scanner import load_strategy_logic
    logic_code = load_strategy_logic()
    if not logic_code: return None
    
    local_vars = {'df': df}
    exec(logic_code, {}, local_vars)
    df = local_vars['df']

    signal_indices = np.where(df['Signal'] == True)[0]
    if len(signal_indices) == 0:
        return None

    close_prices = df['Close'].values
    high_prices = df['High'].values
    low_prices = df['Low'].values
    
    # 최적화 결과 저장용 변수
    best_stats = {}
    max_expectancy = -999.0 # 누적 수익보다 '기대 수익률'이 높은 조합을 우선시

    # 2. 벡터 최적화 루프
    for tp in range(3, 21):
        for sl in range(2, 11):
            wins = 0
            losses = 0
            trade_results = []
            
            for idx in signal_indices:
                if idx + 1 >= len(df): continue
                
                entry_price = close_prices[idx]
                target_price = entry_price * (1 + tp / 100)
                stop_price = entry_price * (1 - sl / 100)
                
                # 향후 60일 데이터 슬라이싱
                future_highs = high_prices[idx+1 : idx+61]
                future_lows = low_prices[idx+1 : idx+61]
                
                win_idx = np.where(future_highs >= target_price)[0]
                loss_idx = np.where(future_lows <= stop_price)[0]
                
                first_win = win_idx[0] if len(win_idx) > 0 else 999
                # 손절은 Low가 도달한 시점을 기준으로 함
                first_loss = loss_idx[0] if len(loss_idx) > 0 else 999
                
                if first_win < first_loss and first_win != 999:
                    wins += 1
                    trade_results.append(tp)
                elif first_loss < first_win and first_loss != 999:
                    losses += 1
                    trade_results.append(-sl)
                else:
                    # 기간 내 도달 못함 (0% 처리 혹은 종가 청산)
                    trade_results.append(0)

            # --- 통계 지표 계산 ---
            trade_count = len(trade_results)
            win_rate = (wins / trade_count * 100) if trade_count > 0 else 0
            
            total_profit = sum([r for r in trade_results if r > 0])
            total_loss = abs(sum([r for r in trade_results if r < 0]))
            
            # 손익비 (Profit Factor)
            profit_factor = round(total_profit / total_loss, 2) if total_loss > 0 else total_profit
            
            # 회당 기대 수익률 (Expectancy)
            expectancy = round(sum(trade_results) / trade_count, 2) if trade_count > 0 else 0
            
            # 전체 누적 수익
            total_ret = sum(trade_results)

            # 기대 수익률이 가장 높은 조합을 '최적'으로 간주
            if expectancy > max_expectancy:
                max_expectancy = expectancy
                best_stats = {
                    'ticker': ticker,
                    'best_tp': tp,
                    'best_sl': sl,
                    'win_rate': round(win_rate, 1),
                    'profit_factor': profit_factor,
                    'expectancy': expectancy,
                    'max_return': total_ret,
                    'trade_count': trade_count
                }

    return best_stats

if __name__ == "__main__":
    ticker = "000270.KS" # 기아 테스트
    import time
    start = time.time()
    res = optimize_vectorized(ticker)
    end = time.time()
    
    if res:
        print(f"⚡ 분석 완료! (소요시간: {end-start:.4f}초)")
        print("📈 [결과 리포트]")
        print(f" - 종목: {res['ticker']}")
        print(f" - 최적 조합: TP {res['best_tp']}% / SL {res['best_sl']}%")
        print(f" - 승률: {res['win_rate']}%")
        print(f" - 손익비: {res['profit_factor']}")
        print(f" - 회당 기대수익률: {res['expectancy']}%")
        print(f" - 2년간 누적수익: {res['max_return']}% (총 {res['trade_count']}회 매매)")
    else:
        print("시그널이 발생하지 않았습니다.")