from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PySide6.QtCore import Qt

class BaseDialog(QDialog):
    """ダイアログのベースクラス"""
    
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        
        # ウィンドウの設定
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        
        # レイアウトの設定
        self.layout = QVBoxLayout(self)
        
        # ボタンボックスの設定
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # OKボタンのデフォルトテキストを「保存」に変更
        self.button_box.button(QDialogButtonBox.Ok).setText("保存")
        self.button_box.button(QDialogButtonBox.Cancel).setText("キャンセル") 