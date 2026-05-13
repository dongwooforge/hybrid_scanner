import os
from utils.config import Config

def load_strategy_logic(filename="my_private_logic.txt"):
    """
    외부 텍스트 파일에서 매매 전략 로직을 읽어옵니다.
    보안과 유지보수를 위해 전략 코드를 메인 엔진과 분리하여 관리합니다.
    """
    # 전략 파일 경로 설정 (기본적으로 프로젝트 루트나 strategy 폴더 내)
    strategy_path = os.path.join(Config.BASE_DIR, "strategy", filename)
    
    # 만약 strategy 폴더 내에 없다면 루트 폴더 확인
    if not os.path.exists(strategy_path):
        strategy_path = os.path.join(Config.BASE_DIR, filename)

    try:
        if os.path.exists(strategy_path):
            with open(strategy_path, "r", encoding="utf-8") as f:
                logic_code = f.read()
            return logic_code
        else:
            # 파일이 없을 경우를 대비한 기본 로직 (골든크로스 예시)
            print(f"⚠️ 전략 파일을 찾을 수 없습니다: {strategy_path}")
            print("ℹ️ 기본 예시 로직으로 대체합니다.")
            return """
df['MA5'] = df['Close'].rolling(window=5).mean()
df['MA20'] = df['Close'].rolling(window=20).mean()
df['Signal'] = (df['MA5'] > df['MA20']) & (df['MA5'].shift(1) <= df['MA20'].shift(1))
            """
    except Exception as e:
        print(f"❌ 로직 로드 중 오류 발생: {e}")
        return None

def get_strategy_metadata(logic_code):
    """
    로직 코드 내의 주석 등을 분석하여 전략의 이름이나 
    설명 같은 메타데이터를 추출할 수 있습니다. (확장용)
    """
    lines = logic_code.strip().split('\n')
    if lines and lines[0].startswith('#'):
        return lines[0].replace('#', '').strip()
    return "Unnamed Strategy"