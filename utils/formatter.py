class Formatter:
    @staticmethod
    def format_currency(value: float, currency: str = "KRW") -> str:
        """금액 포맷팅 (예: 1,234,500)"""
        if currency == "KRW":
            return f"{int(value):,}"
        return f"{value:,.2f}"

    @staticmethod
    def format_percent(value: float) -> str:
        """퍼센트 포맷팅 (예: +15.20%)"""
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.2f}%"