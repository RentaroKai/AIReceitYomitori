"""アプリケーションのエントリーポイント。GUIアプリケーションの起動と初期設定を行う。"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui import MainWindow
from src.utils import logger

# アプリケーション情報
APP_NAME = "AI Receipt Extractor"
APP_VERSION = "1.0.0"

def setup_application():
    """アプリケーションの初期設定を行う"""
    # アプリケーション情報の設定
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)
    
    # 作業ディレクトリの設定
    os.chdir(project_root)

def main():
    """アプリケーションのメインエントリーポイント"""
    print ("かいし★")
    # QApplicationインスタンスの作成
    app = QApplication(sys.argv)
    
    # アプリケーションの初期設定
    setup_application()
    
    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()
    
    logger.info("アプリケーションを起動しました")
    
    # イベントループの開始
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 