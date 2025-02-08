from PySide6.QtWidgets import QLabel, QVBoxLayout, QProgressBar, QDialogButtonBox
from PySide6.QtCore import Qt, QTimer, Signal
from src.ui.dialogs.base_dialog import BaseDialog

class ProcessingDialog(BaseDialog):
    """処理中ダイアログ"""
    
    # キャンセルシグナルを追加
    cancelled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent, "処理中")
        
        # ウィンドウの設定
        self.setModal(True)
        
        # キャンセルボタンのみ表示
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel)
        self.button_box.rejected.connect(self._on_cancel)
        
        # UIの構築
        self._setup_ui()
        
        # アニメーションタイマー
        self._dots_count = 0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_dots)
        self._animation_timer.start(500)  # 0.5秒ごとに更新
        
        # キャンセルフラグ
        self._cancelled = False
        
        # 自動クローズフラグ
        self._auto_close = False
    
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
        self.layout.addWidget(self.button_box)
        
        # サイズの調整
        self.resize(300, 100)
    
    def _update_dots(self):
        """ドットアニメーションの更新"""
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count
        self.message_label.setText(f"画像を処理しています{dots}")
    
    def _on_cancel(self):
        """キャンセルボタンが押されたときの処理"""
        self._cancelled = True
        self.cancelled.emit()
    
    def is_cancelled(self):
        """キャンセルされたかどうかを返す"""
        return self._cancelled
    
    def set_auto_close(self, auto_close: bool):
        """自動クローズフラグを設定"""
        self._auto_close = auto_close
    
    def closeEvent(self, event):
        """ダイアログが閉じられるときの処理"""
        # 自動クローズでない場合のみキャンセル処理を実行
        if not self._auto_close:
            self._on_cancel()
        self._animation_timer.stop()
        super().closeEvent(event) 