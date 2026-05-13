
from utils.config import Config
from core.fetcher import update_ticker_list, update_all_tickers
from core.scanner import scan_tickers
from core.optimizer import optimize_vectorized

def run_cli_pipeline():
    """
    서버 자동화용 파이프라인:
    티커 갱신 -> 데이터 수집 -> 전략 스캔 -> 최적화 분석 -> 결과 출력
    """
    print(f"--- 🚀 Hybrid Scanner V2 가동 (모드: {Config.MARKET_MODE}) ---")

    # 1. 티커 리스트 최신화
    if not update_ticker_list():
        print("❌ 티커 리스트 갱신 실패")
        return

    # 2. 전 종목 데이터 수집 (숫자 진행률 표시됨)
    update_all_tickers()

    # 3. 전략 스캔 (Signal 포착)
    detected_list = scan_tickers()
    
    if not detected_list:
        print("📭 오늘 포착된 시그널이 없습니다.")
        return

    # 4. 결과 분석 및 리포트 생성
    print(f"\n--- 📊 최종 리포트 ({len(detected_list)} 종목 포착) ---")
    print("-" * 60)
    print(f"{'티커':<12} | {'현재가':<10} | {'최적TP':<6} | {'최적SL':<6} | {'예상수익'}")
    print("-" * 60)

    for item in detected_list:
        ticker = item['ticker']
        # 초고속 벡터 최적화 실행
        opt_res = optimize_vectorized(ticker)
        
        if opt_res:
            print(f"{ticker:<12} | {item['price']:>10,.0f} | {opt_res['best_tp']:>5}% | "
                  f"{opt_res['best_sl']:>5}% | {opt_res['max_return']:>7}%")
    
    print("-" * 60)
    print("✅ 모든 분석이 완료되었습니다.")

if __name__ == "__main__":
    # 환경 변수 등에 따라 실행 모드를 분기하거나 바로 파이프라인 실행
    run_cli_pipeline()