#scanner.py
import os
import pandas as pd
from utils.config import Config
from strategy.logic_loader import load_strategy_logic  # 명시적 임포트


"""
================================================================================
[ MODULE : core/scanner.py ]
- 역할: 저장된 CSV 데이터를 순회하며 외부 전략 로직(.txt)을 실행, 매수 시그널 포착
- 연계: strategy/logic_loader.py(로직 공급), storage/(데이터 읽기)
================================================================================
1. INPUT (입력)
   - Data Source: storage/{MARKET_MODE} 내의 모든 _{INTERVAL}.csv 파일들
   - Strategy: strategy/my_private_logic.txt (사용자 정의 매매 조건문)


================================================================================
2. OUTPUT (출력)
   - Return Value: list of dict
     ㄴ 구조: [{'ticker': '005930.KS', 'name': '삼성전자', 'price': 72000, ...}]
================================================================================


3. 연계 작용 (Data Flow)
   - [IN]  strategy/logic_loader -> 텍스트 형태의 파이썬 전략 코드를 읽어옴
   - [IN]  storage/ -> 저장된 과거 시세 데이터를 Pandas DataFrame으로 로드
   - [PROCESS] exec() -> 읽어온 전략 코드를 데이터프레임 위에서 실행하여 'Signal' 열 생성
   - [OUT] ui/threads.py -> 포착된 종목 정보를 UI 리스트에 전달 (다음 공정)
================================================================================
"""


def get_ticker_name_map():
    """
    ticker_list.txt를 읽어 {티커: 종목명} 딕셔너리를 생성합니다.
    """
    ticker_file = Config.get("TICKER_FILE")
    name_map = {}
    if ticker_file.exists():
        with open(ticker_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    name_map[parts[0]] = parts[1]
    return name_map

def scan_tickers():
    """
    현재 시장 모드의 데이터 폴더를 스캔하여 시그널 종목을 반환합니다.
    
    [Output Structure]
    - signals (list of dict):
        [
            {
                'ticker': str (예: '005930.KS'),
                'price': float (현재가/종가),
                'date': str (시그널 발생 날짜 'YYYY-MM-DD')
            },
            ...
        ]
    """
    data_dir = Config.get_path("DATA_DIR")
    
    # strategy/logic_loader.py의 함수를 사용하여 로직 코드를 가져옴
    logic_code = load_strategy_logic("my_private_logic.txt")
    
    if not logic_code:
        print("❌ 실행 가능한 전략 로직이 없습니다.")
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
            # 1. 데이터 로드
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            if len(df) < 20: 
                continue
                
            # 2. 전략 로직 실행
            # 로더에서 가져온 logic_code를 exec()로 실행하여 df에 Signal 컬럼 생성
            local_vars = {'df': df}
            exec(logic_code, {}, local_vars)
            df = local_vars['df']
            
            # 3. 최신 시그널 확인
            if 'Signal' not in df.columns:
                print(f"⚠️ {ticker}: 로직 내에 'Signal' 컬럼 정의가 없습니다.")
                continue
            name_map = get_ticker_name_map() # 매핑 데이터 로드    
            last_row = df.iloc[-1]
            if last_row['Signal'] == True:
                signals.append({
                    'ticker': ticker,
                    'name': name_map.get(ticker, "N/A"),
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