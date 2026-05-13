from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

class ScannerTableView:
    """메인 테이블의 디자인 및 데이터 삽입 로직 관리"""
    @staticmethod
    def setup_table(table: QTableWidget):
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    @staticmethod
    def add_row(table: QTableWidget, data: dict):
        row = table.rowCount()
        table.insertRow(row)
        
        # 숫자 정렬 등을 위한 커스텀 설정
        items = [
            data['ticker'],
            f"{data['price']:,}",
            f"{data['best_tp']}%",
            f"{data['best_sl']}%",
            f"{data['max_return']}%"
        ]
        
        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, col, item)