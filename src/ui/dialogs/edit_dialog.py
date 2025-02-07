from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QSpinBox,
    QDateEdit, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

from src.ui.dialogs.base_dialog import BaseDialog
from src.core import data_manager

class EditDialog(BaseDialog):
    """データ編集ダイアログ"""
    
    def __init__(self, parent=None, image_data=None):
        super().__init__(parent, "データ編集")
        
        self.image_data = image_data
        
        # UIの構築
        self._setup_ui()
        
        # データの読み込み
        if image_data:
            self._load_data()
    
    def _setup_ui(self):
        """UIの構築"""
        # 基本情報
        basic_group = QGroupBox("基本情報")
        basic_layout = QFormLayout()
        
        # 取引日
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy/MM/dd")
        basic_layout.addRow("取引日:", self.date_edit)
        
        # 店舗名
        self.store_edit = QLineEdit()
        basic_layout.addRow("店舗名:", self.store_edit)
        
        # 金額
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("¥"))
        self.amount_edit = QSpinBox()
        self.amount_edit.setRange(0, 9999999)
        self.amount_edit.setSingleStep(100)
        amount_layout.addWidget(self.amount_edit)
        basic_layout.addRow("合計金額:", amount_layout)
        
        basic_group.setLayout(basic_layout)
        
        # 税額情報
        tax_group = QGroupBox("税額情報")
        tax_layout = QFormLayout()
        
        # 10%対象
        tax10_layout = QHBoxLayout()
        tax10_layout.addWidget(QLabel("¥"))
        self.tax10_amount = QSpinBox()
        self.tax10_amount.setRange(0, 9999999)
        self.tax10_amount.setSingleStep(100)
        tax10_layout.addWidget(self.tax10_amount)
        tax_layout.addRow("10%対象金額:", tax10_layout)
        
        self.tax10 = QSpinBox()
        self.tax10.setRange(0, 999999)
        tax_layout.addRow("10%消費税額:", self.tax10)
        
        # 8%対象
        tax8_layout = QHBoxLayout()
        tax8_layout.addWidget(QLabel("¥"))
        self.tax8_amount = QSpinBox()
        self.tax8_amount.setRange(0, 9999999)
        self.tax8_amount.setSingleStep(100)
        tax8_layout.addWidget(self.tax8_amount)
        tax_layout.addRow("8%対象金額:", tax8_layout)
        
        self.tax8 = QSpinBox()
        self.tax8.setRange(0, 999999)
        tax_layout.addRow("8%消費税額:", self.tax8)
        
        tax_group.setLayout(tax_layout)
        
        # 編集理由
        reason_group = QGroupBox("編集理由")
        reason_layout = QVBoxLayout()
        
        self.reason_edit = QTextEdit()
        self.reason_edit.setPlaceholderText("編集理由を入力してください")
        reason_layout.addWidget(self.reason_edit)
        
        reason_group.setLayout(reason_layout)
        
        # レイアウトの組み立て
        self.layout.addWidget(basic_group)
        self.layout.addWidget(tax_group)
        self.layout.addWidget(reason_group)
        self.layout.addWidget(self.button_box)
        
        # サイズの調整
        self.resize(400, 600)
    
    def _load_data(self):
        """データの読み込み"""
        if not self.image_data:
            return
        
        extracted_data = self.image_data.get("extracted_data", {})
        
        # 取引日
        date_str = extracted_data.get("Transaction Date (yyyy/mm/dd only)")
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y/%m/%d")
                self.date_edit.setDate(QDate(date.year, date.month, date.day))
            except ValueError:
                pass
        
        # 店舗名
        self.store_edit.setText(extracted_data.get("Store Name", ""))
        
        # 金額
        self.amount_edit.setValue(extracted_data.get("Total Amount (currency symbol removed)", 0))
        
        # 税額情報
        self.tax10_amount.setValue(extracted_data.get("The amount subject to 10% tax", 0))
        self.tax10.setValue(extracted_data.get("The amount of consumption tax at the rate of 10%", 0))
        self.tax8_amount.setValue(extracted_data.get("The amount subject to 8% tax", 0))
        self.tax8.setValue(extracted_data.get("The amount of consumption tax at the rate of 8%", 0))
    
    def accept(self):
        """OKボタンが押されたときの処理"""
        if not self.image_data:
            return
        
        # 編集前のデータを保存
        old_data = self.image_data.get("extracted_data", {}).copy()
        
        # 新しいデータの作成
        new_data = {
            "Transaction Date (yyyy/mm/dd only)": self.date_edit.date().toString("yyyy/MM/dd"),
            "Store Name": self.store_edit.text().strip(),
            "Total Amount (currency symbol removed)": self.amount_edit.value(),
            "The amount subject to 10% tax": self.tax10_amount.value(),
            "The amount of consumption tax at the rate of 10%": self.tax10.value(),
            "The amount subject to 8% tax": self.tax8_amount.value(),
            "The amount of consumption tax at the rate of 8%": self.tax8.value(),
            "tax rate": 10 if self.tax10_amount.value() > 0 else 8
        }
        
        # データの更新
        data_manager.update_extracted_data(
            self.image_data["file_info"]["path"],
            new_data
        )
        
        # self.image_dataの更新
        self.image_data["extracted_data"] = new_data
        
        # 編集履歴の追加
        reason = self.reason_edit.toPlainText().strip()
        if not reason:
            reason = "手動編集"
        
        # 変更のあったフィールドのみ履歴に追加
        for key, new_value in new_data.items():
            old_value = old_data.get(key)
            if new_value != old_value:
                data_manager.add_edit_history(
                    self.image_data["file_info"]["path"],
                    key,
                    old_value,
                    new_value,
                    reason
                )
        
        super().accept() 