#scanner.py
import os
import pandas as pd
from utils.config import Config

def load_strategy_logic():
    """
    strategy/my_private_logic.txt 파일을 읽어옵니다.
    """
    # .txt 확장자를 명시적으로 지정
    logic_path = Config.BASE_DIR / "strategy" / "my_private_logic.txt"
    
    if not os.path.exists(logic_path):
        print(f"❌ 전략 로직 파일을 찾을 수 없습니다: {logic_path}")
        return None
            
    with open(logic_path, "r", encoding="utf-8") as f:
        return f.read()

def scan_tickers():
    """
    현재 시장 모드의 데이터 폴더를 스캔하여 시그널 종목을 반환합니다.
    
    [Output Structure]
    - signals (list of dict):
        [
            {
                'ticker': str (예: '005930.KS'),
                'price': float (현재가/종가),
                'date': str (시그널 발생 날짜 'YYYY-MM-DD'),
                'name': str (종목명, 필요 시 매핑)
            },
            ...
        ]
    """
    data_dir = Config.get_path("DATA_DIR")
    logic_code = load_strategy_logic()
    
    if not logic_code:
        return []

    signals = []
    # 데이터 폴더 내의 모든 CSV 파일 목록 (Config의 INTERVAL 기반 파일명 매칭)
    interval = Config.get("INTERVAL")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(f'_{interval}.csv')]
    
    print(f"--- 🔍 [{Config.MARKET_MODE}] 전략 스캔 시작 (대상: {len(csv_files)}개) ---")

    for file_name in csv_files:
        # 파일명에서 티커 추출 (예: 'AAPL_4h.csv' -> 'AAPL')
        ticker = file_name.split(f'_{interval}')[0]
        file_path = data_dir / file_name
        
        try:
            # 1. 데이터 로드 (최소 분석 기간 확보를 위해 전체 로드)
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            if len(df) < 20: 
                continue
                
            # 2. 전략 로직 실행
            local_vars = {'df': df}
            exec(logic_code, {}, local_vars)
            df = local_vars['df']
            
            # 3. 최신 시그널 확인
            if 'Signal' not in df.columns:
                print(f"⚠️ {ticker}: 로직 내에 'Signal' 컬럼 정의가 없습니다.")
                continue
                
            last_row = df.iloc[-1]
            if last_row['Signal'] == True:
                signals.append({
                    'ticker': ticker,
                    'price': round(float(last_row['Close']), 2),
                    'date': df.index[-1].strftime('%Y-%m-%d')
                })
                print(f"✅ 시그널 포착: {ticker} | 가격: {last_row['Close']}")
                
        except Exception as e:
            print(f"⚠️ {ticker} 분석 중 오류: {e}")
            continue
            
    return signals

if __name__ == "__main__":
    # 테스트 실행
    print(f"--- 하이브리드 스캐너 V2 테스트 실행 ({Config.MARKET_MODE}) ---")
    detected = scan_tickers()
    print(f"\n🚀 스캔 완료: {len(detected)} 종목 발견")