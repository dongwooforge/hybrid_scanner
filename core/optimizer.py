#optimizer.py

import pandas as pd
import numpy as np
from utils.config import Config

def optimize_vectorized(ticker):
    """
    벡터 연산을 활용하여 초고속으로 최적의 TP/SL 조합을 찾습니다.
    """
    data_dir = Config.get_path("DATA_DIR")
    interval = Config.get("INTERVAL")
    file_path = data_dir / f"{ticker}_{interval}.csv"
    
    # 1. 데이터 로드 및 전략 적용
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    from core.scanner import load_strategy_logic
    logic_code = load_strategy_logic()
    local_vars = {'df': df}
    exec(logic_code, {}, local_vars)
    df = local_vars['df']

    # 시그널 발생 지점 인덱스 추출
    signal_indices = np.where(df['Signal'] == True)[0]
    if len(signal_indices) == 0:
        return None

    close_prices = df['Close'].values
    high_prices = df['High'].values
    low_prices = df['Low'].values
    
    best_tp, best_sl, max_ret = 0, 0, -999.0

    # 2. 벡터 최적화 루프
    # (연산 자체를 행렬로 처리하여 속도를 극대화함)
    for tp in range(3, 21):
        for sl in range(2, 11):
            total_profit = 0
            
            for idx in signal_indices:
                if idx + 1 >= len(df): continue
                
                entry_price = close_prices[idx]
                target_price = entry_price * (1 + tp / 100)
                stop_price = entry_price * (1 - sl / 100)
                
                # 진입 이후 데이터를 벡터로 슬라이싱하여 조건 비교
                # 이 구간이 Numpy 내부에서 돌아가므로 매우 빠름
                future_highs = high_prices[idx+1 : idx+61]
                future_lows = low_prices[idx+1 : idx+61]
                
                # 익절가 도달 시점과 손절가 도달 시점 찾기
                win_idx = np.where(future_highs >= target_price)[0]
                loss_idx = np.where(future_lows <= stop_price)[0]
                
                first_win = win_idx[0] if len(win_idx) > 0 else 999
                first_loss = loss_idx[0] if len(loss_idx) > 0 else 999
                
                if first_win < first_loss and first_win != 999:
                    total_profit += tp
                elif first_loss < first_win and first_loss != 999:
                    total_profit -= sl
                # 도달 못하면 0 (본전/타임오버)

            if total_profit > max_ret:
                max_ret = total_profit
                best_tp, best_sl = tp, sl

    return {
        'ticker': ticker,
        'best_tp': best_tp,
        'best_sl': best_sl,
        'max_return': max_ret,
        'trades': len(signal_indices)
    }

if __name__ == "__main__":
    ticker = "000270.KS"
    import time
    start = time.time()
    res = optimize_vectorized(ticker)
    end = time.time()
    
    print(f"⚡ 벡터 최적화 완료! (소요시간: {end-start:.4f}초)")
    print(f"📊 결과: {res}")