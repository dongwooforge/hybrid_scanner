import logging
from utils.config import Config

def setup_logger():
    log_path = Config.BASE_DIR / "storage" / "system.log"
    
    # storage 폴더가 없을 경우 대비
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler() # 콘솔에도 출력
        ]
    )
    return logging.getLogger("HybridScanner")