#threads.py


from PyQt6.QtCore import QThread, pyqtSignal
from core.fetcher import update_ticker_list, update_all_tickers
from core.scanner import scan_tickers
from core.optimizer import optimize_vectorized

class ScanWorker(QThread):
    """
    GUI의 응답성을 유지하기 위해 데이터 수집 및 스캔을 
    별도 쓰레드에서 처리하는 클래스입니다.
    """
    # 전송할 데이터 타입 명시
    progress_sig = pyqtSignal(int, str)  # 진행률(%), 현재 작업 메시지
    result_sig = pyqtSignal(dict)        # 개별 종목 분석 결과 (최적화 포함)
    finished_sig = pyqtSignal(int)       # 총 발견 종목 수 전송

    def __init__(self, mode: str = "SCAN"):
        super().__init__()
        self.mode = mode  # "FETCH" 또는 "SCAN"

    def run(self):
        """쓰레드가 시작되면 실행되는 메인 로직"""
        if self.mode == "FETCH":
            self._execute_fetch()
        elif self.mode == "SCAN":
            self._execute_scan()

    def _execute_fetch(self):
        """데이터 수집 로직"""
        self.progress_sig.emit(10, "티커 리스트 업데이트 중...")
        update_ticker_list()
        
        self.progress_sig.emit(30, "데이터 수집 시작 (시간이 다소 소요될 수 있습니다)")
        # 현재 fetcher 로직을 수행
        update_all_tickers()
        
        self.progress_sig.emit(100, "모든 데이터 수집 및 업데이트 완료")
        self.finished_sig.emit(0)

    def _execute_scan(self):
        """전략 스캔 및 벡터 최적화 로직"""
        self.progress_sig.emit(5, "전략 로직 로드 및 파일 스캔 중...")
        
        # 1. 1차 필터링 (Signal 발생 종목 추출)
        detected_list = scan_tickers()
        total = len(detected_list)
        
        if total == 0:
            self.progress_sig.emit(100, "포착된 시그널이 없습니다.")
            self.finished_sig.emit(0)
            return

        # 2. 포착된 종목별로 즉시 최적화(Optimizer) 실행
        for i, item in enumerate(detected_list, 1):
            ticker = item['ticker']
            
            # 초고속 벡터 최적화 호출
            opt_res = optimize_vectorized(ticker)
            
            if opt_res:
                # 시그널 데이터와 최적화 결과 병합
                # 딕셔너리 언패킹(Unpacking)을 통한 명시적 결합
                final_data = {
                    'ticker': ticker,
                    'price': item['price'],
                    'date': item['date'],
                    'best_tp': opt_res['best_tp'],
                    'best_sl': opt_res['best_sl'],
                    'max_return': opt_res['max_return']
                }
                self.result_sig.emit(final_data)
            
            # 진행률 계산 및 UI 전송
            progress_pct = int((i / total) * 100)
            self.progress_sig.emit(progress_pct, f"[{ticker}] 최적화 분석 완료")

        self.finished_sig.emit(total)