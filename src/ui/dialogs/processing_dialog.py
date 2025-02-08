from PySide6.QtWidgets import QLabel, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QTimer
from src.ui.dialogs.base_dialog import BaseDialog

class ProcessingDialog(BaseDialog):
    """処理中ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "処理中")
        
        # ウィンドウの設定
        self.setModal(True)
        self.button_box.hide()  # ボタンを非表示
        
        # UIの構築
        self._setup_ui()
        
        # アニメーションタイマー
        self._dots_count = 0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_dots)
        self._animation_timer.start(500)  # 0.5秒ごとに更新
    
    def _setup_ui(self):
        """UIの構築"""
        # メッセージラベル
        self.message_label = QLabel("画像を処理しています...")
        self.message_label.setAlignment(Qt.AlignCenter)
        
        # インジケーター
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # 不定のプログレスバー
        self.progress_bar.setTextVisible(False)
        
        # レイアウトの組み立て
        self.layout.addWidget(self.message_label)
        self.layout.addWidget(self.progress_bar)
        
        # サイズの調整
        self.resize(300, 100)
    
    def _update_dots(self):
        """ドットアニメーションの更新"""
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count
        self.message_label.setText(f"画像を処理しています{dots}")
    
    def closeEvent(self, event):
        """ダイアログが閉じられるときの処理"""
        self._animation_timer.stop()
        super().closeEvent(event) 