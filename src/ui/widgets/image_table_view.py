from PySide6.QtWidgets import QTableView
from PySide6.QtCore import Qt, Signal

from .image_table_model import ImageTableModel
from .image_table_delegate import ImageTableDelegate
from .custom_header_view import CustomHeaderView

class ImageTableView(QTableView):
    """画像一覧用のテーブルビュー"""
    
    # カスタムシグナル
    reprocess_requested = Signal(dict)  # 再処理リクエスト
    edit_requested = Signal(dict)       # 編集リクエスト
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # モデルの設定
        self._model = ImageTableModel()
        self.setModel(self._model)
        
        # デリゲートの設定
        self._delegate = ImageTableDelegate(self)
        self.setItemDelegate(self._delegate)
        
        # カスタムヘッダービューの設定
        self._header = CustomHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(self._header)
        self._header.sectionClicked.connect(self._on_header_clicked)
        
        # シグナルの接続
        self._delegate.reprocess_requested.connect(self.reprocess_requested)
        self._delegate.edit_requested.connect(self.edit_requested)
        
        # 見た目の設定
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        
        # 列の設定
        self._header.setStretchLastSection(True)
        self._header.setSectionsMovable(True)
        
        # 列幅の初期設定
        self.setColumnWidth(0, 30)   # チェックボックス
        self.setColumnWidth(1, 50)   # ステータス（文字表示）
        self.setColumnWidth(2, 60)   # プレビュー（表示ボタン）
        self.setColumnWidth(3, 200)  # ファイル名
        self.setColumnWidth(4, 150)  # 店舗名
        self.setColumnWidth(5, 100)  # 取引日
        self.setColumnWidth(6, 100)
        self.setColumnWidth(7, 100)  # 10%消費税額
        self.setColumnWidth(8, 100)  # 8%消費税額
        self.setColumnWidth(9, 100)  # 10%対象額
        self.setColumnWidth(10, 100) # 8%対象額
        self.setColumnWidth(11, 150) # 商品名
        self.setColumnWidth(12, 100) # 処理状態
        self.setColumnWidth(13, 120) # 操作

        # 処理状態列を非表示に設定
        self.set_column_visible("process_status", False)
        # 操作列を非表示に設定
        self.set_column_visible("actions", False)
    
    def add_image(self, image_data: dict):
        """画像データを追加"""
        self._model.add_image(image_data)
    
    def clear(self):
        """全データをクリア"""
        self._model.clear()
    
    def get_checked_items(self) -> list:
        """チェックされた項目を取得"""
        return self._model.get_checked_items()
    
    def check_all(self):
        """全項目をチェック"""
        self._model.check_all()
    
    def uncheck_all(self):
        """全項目のチェックを解除"""
        self._model.uncheck_all()
    
    def set_column_visible(self, column_id: str, visible: bool):
        """列の表示/非表示を設定"""
        for i, column in enumerate(self._model.COLUMNS):
            if column["id"] == column_id:
                self.setColumnHidden(i, not visible)
                break
    
    def get_column_visible(self, column_id: str) -> bool:
        """列の表示/非表示状態を取得"""
        for i, column in enumerate(self._model.COLUMNS):
            if column["id"] == column_id:
                return not self.isColumnHidden(i)
        return False

    def _on_header_clicked(self, logical_index: int):
        """ヘッダーがクリックされたときの処理"""
        if logical_index == 0:  # チェックボックス列
            # 現在の状態を取得
            header_state = self._model.headerData(0, Qt.Horizontal, Qt.CheckStateRole)
            # 反転した状態を設定
            new_state = Qt.Unchecked if header_state == Qt.Checked else Qt.Checked
            self._model.setHeaderData(0, Qt.Horizontal, new_state, Qt.CheckStateRole) 