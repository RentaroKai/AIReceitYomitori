from typing import Any, List, Optional
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QIcon
import os

class ImageTableModel(QAbstractTableModel):
    """画像一覧用のテーブルモデル"""
    
    # カラム定義
    COLUMNS = [
        {"id": "checkbox", "name": "", "type": Qt.CheckStateRole},
        {"id": "status", "name": "状態", "type": Qt.DisplayRole},
        {"id": "preview", "name": "プレビュー", "type": Qt.DisplayRole},
        {"id": "filename", "name": "ファイル名", "type": Qt.DisplayRole},
        {"id": "store", "name": "店舗名", "type": Qt.DisplayRole},
        {"id": "date", "name": "取引日", "type": Qt.DisplayRole},
        {"id": "amount", "name": "金額", "type": Qt.DisplayRole},
        {"id": "tax_10", "name": "10%消費税額", "type": Qt.DisplayRole},
        {"id": "tax_8", "name": "8%消費税額", "type": Qt.DisplayRole},
        {"id": "tax_base_10", "name": "10%対象額", "type": Qt.DisplayRole},
        {"id": "tax_base_8", "name": "8%対象額", "type": Qt.DisplayRole},
        {"id": "process_status", "name": "処理状態", "type": Qt.DisplayRole},
        {"id": "actions", "name": "操作", "type": Qt.UserRole}
    ]
    
    # ステータスの表示文字列
    STATUS_DISPLAY = {
        "pending": "未処理",
        "processing": "処理中",
        "completed": "完了",
        "error": "エラー"
    }
    
    def __init__(self):
        super().__init__()
        self._data: List[dict] = []
        self._checked_rows: set = set()
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """行数を返す"""
        return len(self._data)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """列数を返す"""
        return len(self.COLUMNS)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """セルのデータを返す"""
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        column = self.COLUMNS[col]
        
        if column["id"] == "checkbox":
            if role == Qt.CheckStateRole:
                is_checked = row in self._checked_rows
                return Qt.Checked if is_checked else Qt.Unchecked
            return None
        
        if role == Qt.DisplayRole:
            if column["id"] == "status":
                # ステータスの文字列を返す
                status = self._data[row].get("processing_status", {}).get("status", "pending")
                return self.STATUS_DISPLAY.get(status, "不明")
            elif column["id"] == "preview":
                # プレビュー列にはファイル名を表示
                file_info = self._data[row].get("file_info", {})
                return os.path.basename(file_info.get("path", ""))
            elif column["type"] == Qt.DisplayRole:
                extracted_data = self._data[row].get("extracted_data", {})
                if column["id"] == "amount":
                    # 金額の場合は数値を通貨形式で表示
                    amount = extracted_data.get("Total Amount (currency symbol removed)")
                    return f"¥{amount:,}" if amount is not None else ""
                elif column["id"] == "tax_10":
                    amount = extracted_data.get("The amount of consumption tax at the rate of 10%")
                    return f"¥{amount:,}" if amount is not None else ""
                elif column["id"] == "tax_8":
                    amount = extracted_data.get("The amount of consumption tax at the rate of 8%")
                    return f"¥{amount:,}" if amount is not None else ""
                elif column["id"] == "tax_base_10":
                    amount = extracted_data.get("The amount subject to 10% tax")
                    return f"¥{amount:,}" if amount is not None else ""
                elif column["id"] == "tax_base_8":
                    amount = extracted_data.get("The amount subject to 8% tax")
                    return f"¥{amount:,}" if amount is not None else ""
                elif column["id"] == "store":
                    return extracted_data.get("Store Name", "")
                elif column["id"] == "date":
                    return extracted_data.get("Transaction Date (yyyy/mm/dd only)", "")
                elif column["id"] == "filename":
                    file_path = self._data[row].get("file_info", {}).get("path", "")
                    return os.path.basename(file_path)
                elif column["id"] == "process_status":
                    status = self._data[row].get("processing_status", {})
                    if status.get("error_type"):
                        return f"エラー: {status.get('error_details', '')}"
                    return status.get("status", "pending")
                return self._data[row].get(column["id"], "")
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """ヘッダーのデータを返す"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]["name"]
        return None
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """セルのフラグを返す"""
        if not index.isValid():
            return Qt.NoItemFlags
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        # チェックボックス列の場合
        if self.COLUMNS[index.column()]["id"] == "checkbox":
            flags |= Qt.ItemIsUserCheckable
        
        # 編集可能なカラム
        editable_columns = ["store", "date", "amount", "tax_10", "tax_8", "tax_base_10", "tax_base_8"]
        if self.COLUMNS[index.column()]["id"] in editable_columns:
            flags |= Qt.ItemIsEditable
        
        return flags
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """セルのデータを設定"""
        if not index.isValid():
            return False
        
        # チェックボックス列の場合
        if self.COLUMNS[index.column()]["id"] == "checkbox":
            if role == Qt.CheckStateRole:
                row = index.row()
                
                # 現在の状態を反転
                if row in self._checked_rows:
                    self._checked_rows.discard(row)
                else:
                    self._checked_rows.add(row)
                
                self.dataChanged.emit(index, index, [role])
                return True
        
        # 編集可能なカラムの場合
        if role == Qt.EditRole:
            column_id = self.COLUMNS[index.column()]["id"]
            row = index.row()
            
            # 編集前のデータを保存
            old_data = self._data[row].get("extracted_data", {}).copy()
            
            # データの更新
            if column_id == "store":
                self._data[row]["extracted_data"]["Store Name"] = str(value)
            elif column_id == "date":
                self._data[row]["extracted_data"]["Transaction Date (yyyy/mm/dd only)"] = str(value)
            elif column_id == "amount":
                try:
                    amount = int(str(value).replace("¥", "").replace(",", ""))
                    self._data[row]["extracted_data"]["Total Amount (currency symbol removed)"] = amount
                except ValueError:
                    return False
            elif column_id == "tax_10":
                try:
                    amount = int(str(value).replace("¥", "").replace(",", ""))
                    self._data[row]["extracted_data"]["The amount of consumption tax at the rate of 10%"] = amount
                except ValueError:
                    return False
            elif column_id == "tax_8":
                try:
                    amount = int(str(value).replace("¥", "").replace(",", ""))
                    self._data[row]["extracted_data"]["The amount of consumption tax at the rate of 8%"] = amount
                except ValueError:
                    return False
            elif column_id == "tax_base_10":
                try:
                    amount = int(str(value).replace("¥", "").replace(",", ""))
                    self._data[row]["extracted_data"]["The amount subject to 10% tax"] = amount
                except ValueError:
                    return False
            elif column_id == "tax_base_8":
                try:
                    amount = int(str(value).replace("¥", "").replace(",", ""))
                    self._data[row]["extracted_data"]["The amount subject to 8% tax"] = amount
                except ValueError:
                    return False
            
            # データマネージャーの更新
            from src.core import data_manager
            data_manager.update_extracted_data(
                self._data[row]["file_info"]["path"],
                self._data[row]["extracted_data"]
            )
            
            # 編集履歴の追加
            data_manager.add_edit_history(
                self._data[row]["file_info"]["path"],
                column_id,
                old_data.get(column_id),
                self._data[row]["extracted_data"].get(column_id),
                "直接編集"
            )
            
            self.dataChanged.emit(index, index, [role])
            return True
        
        return False
    
    def add_image(self, image_data: dict):
        """画像データを追加"""
        row = len(self._data)
        self.beginInsertRows(QModelIndex(), row, row)
        self._data.append(image_data)
        self.endInsertRows()
    
    def clear(self):
        """全データをクリア"""
        self.beginResetModel()
        self._data.clear()
        self._checked_rows.clear()
        self.endResetModel()
    
    def get_checked_items(self) -> List[dict]:
        """チェックされた項目を取得"""
        return [self._data[row] for row in sorted(self._checked_rows)]
    
    def check_all(self):
        """全項目をチェック"""
        self._checked_rows = set(range(len(self._data)))
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.CheckStateRole]
        )
    
    def uncheck_all(self):
        """全項目のチェックを解除"""
        self._checked_rows.clear()
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
            [Qt.CheckStateRole]
        ) 