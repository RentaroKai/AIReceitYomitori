from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from pathlib import Path
from src.ui.dialogs.base_dialog import BaseDialog
from src.utils.logger import logger

class LogViewerDialog(BaseDialog):
    """ログビューワーダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "ログビューワー")
        
        # UIの構築
        self._setup_ui()
        
        # ログファイルの監視タイマー
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_log)
        self._update_timer.start(1000)  # 1秒ごとに更新
        
        # 初期表示
        self._update_log()
    
    def _setup_ui(self):
        """UIの構築"""
        # テキストブラウザの作成
        self.text_browser = QTextBrowser()
        self.text_browser.setLineWrapMode(QTextBrowser.NoWrap)
        self.text_browser.setFont(self.font())
        
        # ボタンの作成
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self._clear_log)
        button_layout.addWidget(self.clear_button)
        
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self._update_log)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        
        # レイアウトの組み立て
        self.layout.addWidget(self.text_browser)
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.button_box)
        
        # サイズの調整
        self.resize(800, 600)
    
    def _update_log(self):
        """ログの更新"""
        try:
            log_file = logger._log_file
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.text_browser.setText(content)
                    # 最下部にスクロール
                    self.text_browser.verticalScrollBar().setValue(
                        self.text_browser.verticalScrollBar().maximum()
                    )
        except Exception as e:
            self.text_browser.setText(f"ログファイルの読み込みに失敗しました: {str(e)}")
    
    def _clear_log(self):
        """ログのクリア"""
        try:
            log_file = logger._log_file
            if log_file.exists():
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("")
                self.text_browser.clear()
        except Exception as e:
            self.text_browser.setText(f"ログファイルのクリアに失敗しました: {str(e)}")
    
    def closeEvent(self, event):
        """ダイアログが閉じられるときの処理"""
        self._update_timer.stop()
        super().closeEvent(event) 