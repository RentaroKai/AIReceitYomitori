import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import config

class Logger:
    """ロギング管理クラス"""
    
    def __init__(self):
        self._logger = logging.getLogger("AIReceiptExtractor")
        self._logger.setLevel(logging.DEBUG)
        
        # 既存のハンドラーをクリア
        self._logger.handlers.clear()
        
        # ログディレクトリの設定
        self._log_dir = Path(config.get("backup.directory")).parent / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # ログファイル名の設定
        self._log_file = self._log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        
        # ハンドラーの設定
        self._setup_handlers()
        
        # フォーマッターの設定
        self._setup_formatter()
    
    def _setup_handlers(self):
        """ログハンドラーの設定"""
        # ファイルハンドラー（日次ローテーション）
        file_handler = logging.handlers.TimedRotatingFileHandler(
            self._log_file,
            when="midnight",
            interval=1,
            backupCount=7,  # 1週間分保持
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(file_handler)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        self._logger.addHandler(console_handler)
    
    def _setup_formatter(self):
        """ログフォーマッターの設定"""
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        for handler in self._logger.handlers:
            handler.setFormatter(formatter)
    
    def debug(self, message: str, error: Optional[Exception] = None):
        """デバッグログを出力"""
        if error:
            self._logger.debug(f"{message}: {str(error)}")
        else:
            self._logger.debug(message)
    
    def info(self, message: str):
        """情報ログを出力"""
        self._logger.info(message)
    
    def warning(self, message: str, error: Optional[Exception] = None):
        """警告ログを出力"""
        if error:
            self._logger.warning(f"{message}: {str(error)}")
        else:
            self._logger.warning(message)
    
    def error(self, message: str, error: Optional[Exception] = None):
        """エラーログを出力"""
        if error:
            self._logger.error(f"{message}: {str(error)}")
        else:
            self._logger.error(message)
    
    def critical(self, message: str, error: Optional[Exception] = None):
        """重大エラーログを出力"""
        if error:
            self._logger.critical(f"{message}: {str(error)}")
        else:
            self._logger.critical(message)

# シングルトンインスタンス
logger = Logger() 