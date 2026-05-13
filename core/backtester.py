# backtester.py

import pandas as pd

from utils.config import Config

def run_backtest(ticker, target_profit=10.0, stop_loss=5.0):
    """
    특정 종목의 과거 시그널을 전수 조사하여 승률을 계산합니다.
    - target_profit: 목표 수익률 (%)
    - stop_loss: 손절 제한 (%)
    """
    data_dir = Config.get_path("DATA_DIR")
    interval = Config.get("INTERVAL")
    file_path = data_dir / f"{ticker}_{interval}.csv"
    
    # 1. 데이터 로드 및 전략 재적용
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    
    # 전략 로직 로드 (scanner와 동일한 로직 사용)
    from core.scanner import load_strategy_logic
    logic_code = load_strategy_logic()
    local_vars = {'df': df}
    exec(logic_code, {}, local_vars)
    df = local_vars['df']
    
    # 2. 시그널 발생 지점 추출 (어제까지의 데이터만)
    sig_dates = df.index[df['Signal'] == True].tolist()
    
    results = []
    
    # 3. 각 시그널 이후의 흐름 추적
    for entry_date in sig_dates:
        # 진입일 다음날부터 데이터 슬라이싱
        after_entry = df.loc[entry_date:].iloc[1:]
        if after_entry.empty: continue
        
        entry_price = df.loc[entry_date, 'Close']
        tp_price = entry_price * (1 + target_profit / 100)
        sl_price = entry_price * (1 - stop_loss / 100)
        
        outcome = "HOLD" # 아직 결과 안 남
        days_held = 0
        
        for date, row in after_entry.iterrows():
            days_held += 1
            if row['High'] >= tp_price:
                outcome = "WIN"
                break
            elif row['Low'] <= sl_price:
                outcome = "LOSS"
                break
            # 너무 오래 보유하는 경우 방지 (예: 60거래일)
            if days_held >= 60:
                outcome = "TIME_OVER"
                break
        
        results.append({
            'entry_date': entry_date.strftime('%Y-%m-%d'),
            'entry_price': entry_price,
            'outcome': outcome,
            'days': days_held
        })
    
    return results

# --- [테스트 코드] ---
if __name__ == "__main__":
    ticker = "000270.KS" # 방금 포착된 기아차
    print(f"--- {ticker} 백테스트 시작 (익절 10%, 손절 5%) ---")
    backtest_results = run_backtest(ticker)
    
    for res in backtest_results:
        print(f"진입: {res['entry_date']} | 결과: {res['outcome']} ({res['days']}일 보유)")