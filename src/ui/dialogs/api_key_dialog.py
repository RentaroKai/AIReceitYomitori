from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QRadioButton,
    QButtonGroup, QVBoxLayout, QHBoxLayout, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import os

from src.ui.dialogs.base_dialog import BaseDialog
from src.utils import config
import logging

logger = logging.getLogger(__name__)

class APIKeyDialog(BaseDialog):
    """APIキー設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "APIキー設定")
        
        # UIの構築
        self._setup_ui()
        
        # 現在の設定を読み込み
        self._load_current_settings()
    
    def _setup_ui(self):
        """UIの構築"""
        # Google AI Studioへのリンク
        link_layout = QHBoxLayout()
        link_label = QLabel("APIキーの取得は")
        link_button = QLabel("<a href='https://aistudio.google.com/prompts/new_chat'>Google AI Studio</a>")
        link_button.setOpenExternalLinks(True)
        link_end_label = QLabel("から行えます")
        link_layout.addWidget(link_label)
        link_layout.addWidget(link_button)
        link_layout.addWidget(link_end_label)
        link_layout.addStretch()
        
        # APIキーの保存方法選択
        storage_group = QGroupBox("APIキーの保存方法")
        storage_layout = QVBoxLayout()
        
        self.env_radio = QRadioButton("環境変数から読み込む")
        self.manual_radio = QRadioButton("手動で入力")
        
        storage_layout.addWidget(self.env_radio)
        storage_layout.addWidget(self.manual_radio)
        storage_group.setLayout(storage_layout)
        
        # ラジオボタンのグループ化
        self.storage_group = QButtonGroup()
        self.storage_group.addButton(self.env_radio, 0)
        self.storage_group.addButton(self.manual_radio, 1)
        self.storage_group.buttonClicked.connect(self._on_storage_changed)
        
        # APIキー入力フィールド
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("APIキー:"))
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        key_layout.addWidget(self.key_edit)
        
        # 環境変数名
        env_layout = QHBoxLayout()
        env_layout.addWidget(QLabel("環境変数名:"))
        self.env_name_edit = QLineEdit("GOOGLE_API_KEY")
        self.env_name_edit.setPlaceholderText("GOOGLE_API_KEY")
        env_layout.addWidget(self.env_name_edit)
        
        # レイアウトの組み立て
        self.layout.addLayout(link_layout)
        self.layout.addWidget(storage_group)
        self.layout.addLayout(env_layout)
        self.layout.addLayout(key_layout)
        self.layout.addWidget(self.button_box)
    
    def _load_current_settings(self):
        """現在の設定を読み込む"""
        # 環境変数の確認
        env_key = os.getenv("GOOGLE_API_KEY")
        if env_key:
            self.env_radio.setChecked(True)
            self.key_edit.setEnabled(False)
        else:
            self.manual_radio.setChecked(True)
            self.env_name_edit.setEnabled(False)
        
        # 保存されているAPIキーの読み込み
        saved_key = config.get("api.key")
        if saved_key:
            self.key_edit.setText(saved_key)
    
    def _on_storage_changed(self, button):
        """保存方法が変更されたときの処理"""
        is_env = button == self.env_radio
        self.env_name_edit.setEnabled(is_env)
        self.key_edit.setEnabled(not is_env)
    
    def accept(self):
        """OKボタンが押されたときの処理"""
        try:
            if self.manual_radio.isChecked():
                # 手動入力の場合
                api_key = self.key_edit.text().strip()
                if not api_key:
                    logger.error("APIキーが入力されていません")
                    return
                
                # 設定を保存
                config.set("api.key", api_key)
                logger.info("APIキーを設定に保存しました")
            else:
                # 環境変数の場合
                env_name = self.env_name_edit.text().strip()
                if not env_name:
                    logger.error("環境変数名が入力されていません")
                    return
                
                # 環境変数名を保存
                config.set("api.env_name", env_name)
                config.set("api.key", None)  # 手動設定をクリア
                logger.info(f"環境変数名 {env_name} を設定に保存しました")
            
            super().accept()
        
        except Exception as e:
            logger.error("APIキー設定の保存に失敗しました", e) 