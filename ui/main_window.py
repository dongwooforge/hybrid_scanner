#main_window.py

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QComboBox, QPushButton, QLabel, QTableWidget, 
    QTableWidgetItem, QTextEdit, QStatusBar, QHeaderView,
    QApplication
)

from utils.config import Config
from ui.threads import ScanWorker  # 백그라운드 일꾼

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None  # 쓰레드 참조 저장용
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle("Hybrid Scanner V2 - Quant Framework")
        self.setMinimumSize(1000, 700)

        # 메인 위젯 및 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # --- [1. 상단 컨트롤 바] ---
        ctrl_layout = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["KR", "US"])
        self.mode_combo.setCurrentText(Config.MARKET_MODE)
        
        self.btn_update_list = QPushButton("티커 리스트 갱신")
        self.btn_fetch_data = QPushButton("데이터 수집 시작")
        self.btn_scan = QPushButton("전략 스캔 시작")
        
        ctrl_layout.addWidget(QLabel("시장 모드:"))
        ctrl_layout.addWidget(self.mode_combo)
        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(self.btn_update_list)
        ctrl_layout.addWidget(self.btn_fetch_data)
        ctrl_layout.addWidget(self.btn_scan)
        ctrl_layout.addStretch()

        layout.addLayout(ctrl_layout)

        # --- [2. 중앙 결과 테이블] ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["종목(Ticker)", "현재가", "최적 TP", "최적 SL", "수익률 합계"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # --- [3. 하단 로그 디스플레이] ---
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas';")
        layout.addWidget(self.log_display)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비 완료")

    def connect_signals(self):
        """시그널 및 슬롯 연결"""
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.btn_update_list.clicked.connect(self.start_fetch_list)
        self.btn_fetch_data.clicked.connect(self.start_fetch_data)
        self.btn_scan.clicked.connect(self.start_scan)

    # --- [이벤트 핸들러 및 슬롯] ---
    def on_mode_changed(self, mode):
        os.environ["MARKET_MODE"] = mode
        Config.MARKET_MODE = mode
        self.append_log(f"🔄 시장 모드 변경: [{mode}]")
        self.status_bar.showMessage(f"현재 모드: {mode}")

    def start_fetch_list(self):
        from core.fetcher import update_ticker_list
        success = update_ticker_list()
        if success:
            self.append_log("✅ 티커 리스트 갱신 완료")

    def start_fetch_data(self):
        self.append_log("📡 전 종목 데이터 수집 시작 (백그라운드)")
        self.worker = ScanWorker(mode="FETCH")
        self.worker.progress_sig.connect(self.update_ui_status)
        self.worker.start()

    def start_scan(self):
        self.table.setRowCount(0)
        self.append_log("🔍 전략 스캔 및 벡터 최적화 시작...")
        self.worker = ScanWorker(mode="SCAN")
        self.worker.progress_sig.connect(self.update_ui_status)
        self.worker.result_sig.connect(self.add_table_row)
        self.worker.finished_sig.connect(lambda count: self.append_log(f"🚀 스캔 종료: 총 {count}개 종목 포착"))
        self.worker.start()

    def update_ui_status(self, pct, msg):
        self.status_bar.showMessage(f"[{pct}%] {msg}")
        if pct % 10 == 0:  # 로그 부하 감소를 위해 10% 단위로만 기록
            self.append_log(msg)

    def add_table_row(self, data):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # 각 셀에 데이터 입력 (정렬 및 포맷 적용 가능)
        self.table.setItem(row, 0, QTableWidgetItem(data['ticker']))
        self.table.setItem(row, 1, QTableWidgetItem(f"{data['price']:,}"))
        self.table.setItem(row, 2, QTableWidgetItem(f"{data['best_tp']}%"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{data['best_sl']}%"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{data['max_return']}%"))

    def append_log(self, text):
        self.log_display.append(f"[{QTime.currentTime().toString('hh:mm:ss')}] {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())