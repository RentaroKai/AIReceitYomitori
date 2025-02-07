from PySide6.QtWidgets import (
    QWidget, QLabel, QSpinBox, QCheckBox,
    QComboBox, QTabWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

from src.ui.dialogs.base_dialog import BaseDialog
from src.utils import config

class SettingsDialog(BaseDialog):
    """設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "設定")
        
        # UIの構築
        self._setup_ui()
        
        # 現在の設定を読み込み
        self._load_current_settings()
    
    def _setup_ui(self):
        """UIの構築"""
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 一般設定タブ
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # バックアップ設定
        backup_group = QGroupBox("バックアップ設定")
        backup_layout = QFormLayout()
        
        self.backup_generations = QSpinBox()
        self.backup_generations.setRange(3, 10)
        backup_layout.addRow("バックアップ世代数:", self.backup_generations)
        
        backup_group.setLayout(backup_layout)
        general_layout.addWidget(backup_group)
        
        # 画像処理設定
        image_group = QGroupBox("画像処理設定")
        image_layout = QFormLayout()
        
        self.resize_enabled = QCheckBox("画像を自動でリサイズする")
        image_layout.addRow(self.resize_enabled)
        
        self.max_width = QSpinBox()
        self.max_width.setRange(800, 3840)
        self.max_width.setSingleStep(100)
        image_layout.addRow("最大幅:", self.max_width)
        
        self.max_height = QSpinBox()
        self.max_height.setRange(600, 2160)
        self.max_height.setSingleStep(100)
        image_layout.addRow("最大高さ:", self.max_height)
        
        self.image_quality = QSpinBox()
        self.image_quality.setRange(60, 100)
        image_layout.addRow("画質 (%):", self.image_quality)
        
        image_group.setLayout(image_layout)
        general_layout.addWidget(image_group)
        
        # 表示設定タブ
        display_tab = QWidget()
        display_layout = QVBoxLayout(display_tab)
        
        # テーマ設定
        theme_group = QGroupBox("テーマ設定")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ライト", "ダーク"])
        theme_layout.addRow("テーマ:", self.theme_combo)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 16)
        theme_layout.addRow("フォントサイズ:", self.font_size)
        
        theme_group.setLayout(theme_layout)
        display_layout.addWidget(theme_group)
        
        # タブの追加
        self.tab_widget.addTab(general_tab, "一般")
        self.tab_widget.addTab(display_tab, "表示")
        
        # レイアウトの組み立て
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.button_box)
        
        # サイズの調整
        self.resize(400, 500)
    
    def _load_current_settings(self):
        """現在の設定を読み込む"""
        # バックアップ設定
        self.backup_generations.setValue(config.get("backup.generations", 3))
        
        # 画像処理設定
        resize_config = config.get("processing.image.resize", {})
        self.resize_enabled.setChecked(resize_config.get("enabled", True))
        self.max_width.setValue(resize_config.get("max_width", 1920))
        self.max_height.setValue(resize_config.get("max_height", 1080))
        self.image_quality.setValue(resize_config.get("quality", 85))
        
        # 表示設定
        self.theme_combo.setCurrentText(
            "ダーク" if config.get("ui.theme") == "dark" else "ライト"
        )
        self.font_size.setValue(config.get("ui.font_size", 10))
    
    def accept(self):
        """OKボタンが押されたときの処理"""
        # バックアップ設定の保存
        config.set("backup.generations", self.backup_generations.value())
        
        # 画像処理設定の保存
        config.set("processing.image.resize.enabled", self.resize_enabled.isChecked())
        config.set("processing.image.resize.max_width", self.max_width.value())
        config.set("processing.image.resize.max_height", self.max_height.value())
        config.set("processing.image.resize.quality", self.image_quality.value())
        
        # 表示設定の保存
        config.set("ui.theme", "dark" if self.theme_combo.currentText() == "ダーク" else "light")
        config.set("ui.font_size", self.font_size.value())
        
        super().accept() 