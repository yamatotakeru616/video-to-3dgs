# utils/logging_utils.py - ログ設定
import logging
import queue
from datetime import datetime
from pathlib import Path

class QueueHandler(logging.Handler):
    """ログをキューに送信するハンドラー"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        self.log_queue.put(self.format(record))

def setup_logging(log_queue: queue.Queue, log_dir: str = "logs"):
    """ログ設定初期化"""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(
        log_path / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # キューハンドラー（GUI用）
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formatter)
    queue_handler.setLevel(logging.INFO)
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(queue_handler)