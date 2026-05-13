import pandas as pd
from abc import ABC, abstractmethod

class StrategyBase(ABC):
    """
    모든 매매 전략이 상속받아야 하는 추상 기본 클래스입니다.
    신규 전략을 만들 때 이 클래스를 상속받으면 필수로 구현해야 할 메서드가 강제됩니다.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        보조지표(이동평균선, RSI, 볼린저 밴드 등)를 계산하는 메서드입니다.
        """
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        계산된 지표를 바탕으로 'Signal' 컬럼(True/False)을 생성하는 메서드입니다.
        """
        pass

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        지표 계산과 시그널 생성을 순차적으로 실행하는 통합 메서드입니다.
        """
        df = self.calculate_indicators(df)
        df = self.generate_signals(df)
        return df