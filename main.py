
from utils.config import Config
from core.fetcher import update_ticker_list, update_all_tickers
from core.scanner import scan_tickers
from core.optimizer import optimize_vectorized
"""
================================================================================
[ MODULE : main.py ]
- 역할: 공장 전체 공정 총괄 및 '퀀트 스코어보드' 최종 출력
- 연계: core/optimizer.py(지표 수신), storage/ticker_list.txt(종목명 참조)
================================================================================
1. INPUT (입력)
   - Ticker Name: storage/KR/ticker_list.txt 내의 명칭 데이터
   - Quant Data: optimizer.py에서 산출된 5가지 핵심 지표

2. OUTPUT (출력)
   - CLI 리포트: [종목명(티커) | 매매횟수 | 승률 | 손익비 | 기대수익 | TP/SL | 누적수익]

3. 연계 작용 (Data Flow)
   - [MATCH] scanner에서 넘어온 티커를 ticker_list.txt와 대조하여 이름을 입힘
   - [FORMAT] 한글/영문 혼용 시 정렬이 깨지지 않도록 가변 폭 정렬 적용
================================================================================
"""


def get_ticker_name_map():
    """ticker_list.txt에서 {티커: 종목명} 딕셔너리를 생성합니다."""
    ticker_file = Config.get("TICKER_FILE")
    name_map = {}
    if ticker_file.exists():
        with open(ticker_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    name_map[parts[0]] = parts[1]
    return name_map

def run_cli_pipeline():
    print(f"--- 🚀 Hybrid Scanner V2 가동 (모드: {Config.MARKET_MODE}) ---")

    # 1. 티커 및 데이터 업데이트 (필요 시 실행)
    # update_ticker_list()
    # update_all_tickers()

    # 2. 전략 스캔
    detected_list = scan_tickers()
    if not detected_list:
        print("📭 오늘 포착된 시그널이 없습니다.")
        return

    # 종목명 매핑 데이터 로드
    name_map = get_ticker_name_map()

    # 3. 결과 분석 및 리포트 생성
    print(f"\n--- 📊 퀀트 스코어 리포트 ({len(detected_list)} 종목 포착) ---")
    print("=" * 125)
    # 헤더 구성: 종목명 포함
    header = f"{'종목명(티커)':<20} | {'횟수':>4} | {'승률':>6} | {'손익비':>6} | {'회당기대':>8} | {'최적TP/SL':>10} | {'누적수익'}"
    print(header)
    print("-" * 125)

    for item in detected_list:
        ticker = item['ticker']
        name = name_map.get(ticker, "N/A") # 종목명 매핑
        
        # 상세 지표가 포함된 최적화 실행
        opt = optimize_vectorized(ticker)
        
        if opt:
            # 출력용 이름 구성 (예: 삼성전자(005930.KS))
            display_name = f"{name[:8]}({ticker})"
            tp_sl = f"{opt['best_tp']}%/{opt['best_sl']}%"
            
            print(f"{display_name:<20} | {opt['trade_count']:>6} | {opt['win_rate']:>7}% | "
                  f"{opt['profit_factor']:>8} | {opt['expectancy']:>9}% | {tp_sl:>12} | {opt['max_return']:>9}%")
    
    print("=" * 125)
    print("✅ 모든 분석이 완료되었습니다. (회당기대 0.5% 이상 종목에 주목하세요!)")

if __name__ == "__main__":
    run_cli_pipeline()