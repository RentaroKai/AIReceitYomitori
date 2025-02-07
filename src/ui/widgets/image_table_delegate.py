from PySide6.QtWidgets import (
    QStyledItemDelegate, QStyleOptionViewItem,
    QPushButton, QWidget, QHBoxLayout, QStyle
)
from PySide6.QtCore import Qt, QSize, QRect, Signal, QEvent
from PySide6.QtGui import QPainter, QIcon, QPixmap, QColor
import os
import subprocess

class ImageTableDelegate(QStyledItemDelegate):
    """画像一覧用のカスタムデリゲート"""
    
    # シグナル定義
    preview_requested = Signal(str)  # プレビューリクエスト
    reprocess_requested = Signal(dict)  # 再処理リクエスト
    edit_requested = Signal(dict)  # 編集リクエスト
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._link_color = QColor(0, 0, 255)  # リンクの色（青）
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """セルの描画"""
        column_id = index.model().COLUMNS[index.column()]["id"]
        
        if column_id == "preview":
            # プレビュー列はリンクスタイルで描画
            text = index.data(Qt.DisplayRole)
            if text:
                option = QStyleOptionViewItem(option)
                self.initStyleOption(option, index)
                
                # マウスホバー時の背景を描画
                if option.state & QStyle.State_MouseOver:
                    painter.fillRect(option.rect, option.palette.alternateBase())
                
                # リンクスタイルのテキストを描画
                painter.save()
                painter.setPen(self._link_color)
                font = painter.font()
                font.setUnderline(True)
                painter.setFont(font)
                painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, text)
                painter.restore()
            return
        elif column_id == "actions":
            # アクションボタンはcreateEditorで作成
            pass
        else:
            super().paint(painter, option, index)
    
    def editorEvent(self, event, model, option, index) -> bool:
        """マウスイベントの処理"""
        if index.model().COLUMNS[index.column()]["id"] == "preview":
            if event.type() == QEvent.Type.MouseButtonRelease:
                # クリック時に画像を開く
                image_data = model._data[index.row()]
                image_path = image_data.get("file_info", {}).get("path")
                if image_path:
                    try:
                        os.startfile(image_path)
                    except Exception:
                        subprocess.run(['start', '', image_path], shell=True)
                return True
        return super().editorEvent(event, model, option, index)
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index) -> QWidget:
        """エディターの作成"""
        column_id = index.model().COLUMNS[index.column()]["id"]
        
        if column_id == "preview":
            return None  # プレビュー列はエディターを作成しない
        elif column_id == "actions":
            return self._create_action_buttons(parent)
        
        return super().createEditor(parent, option, index)
    
    def _create_preview_button(self, parent: QWidget, index) -> QWidget:
        """プレビューボタンの作成"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # プレビューボタン
        preview_btn = QPushButton("表示", widget)
        preview_btn.setFixedHeight(24)
        preview_btn.clicked.connect(lambda: self._on_preview_clicked(index))
        layout.addWidget(preview_btn)
        
        return widget
    
    def _create_action_buttons(self, parent: QWidget) -> QWidget:
        """アクションボタンの作成"""
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 再処理ボタン
        reprocess_btn = QPushButton("再処理", widget)
        reprocess_btn.setFixedHeight(24)
        reprocess_btn.clicked.connect(lambda: self._on_reprocess_clicked(self.parent().currentIndex()))
        layout.addWidget(reprocess_btn)
        
        # 編集ボタン
        edit_btn = QPushButton("編集", widget)
        edit_btn.setFixedHeight(24)
        edit_btn.clicked.connect(lambda: self._on_edit_clicked(self.parent().currentIndex()))
        layout.addWidget(edit_btn)
        
        return widget
    
    def _on_preview_clicked(self, index):
        """プレビューボタンがクリックされたときの処理"""
        # 画像パスを取得
        image_path = index.model()._data[index.row()]["file_info"]["path"]
        
        # Windowsのデフォルトアプリケーションで開く
        try:
            os.startfile(image_path)
        except Exception:
            # osモジュールのstartfileが使えない場合はsubprocessを使用
            subprocess.run(['start', '', image_path], shell=True)
    
    def _on_reprocess_clicked(self, index):
        """再処理ボタンがクリックされたときの処理"""
        if not index.isValid():
            return
        
        # 画像データを取得
        image_data = index.model()._data[index.row()]
        self.reprocess_requested.emit(image_data)
    
    def _on_edit_clicked(self, index):
        """編集ボタンがクリックされたときの処理"""
        if not index.isValid():
            return
        
        # 画像データを取得
        image_data = index.model()._data[index.row()]
        self.edit_requested.emit(image_data)
    
    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """セルのサイズヒント"""
        column_id = index.model().COLUMNS[index.column()]["id"]
        
        if column_id == "preview":
            return QSize(60, 32)
        elif column_id == "actions":
            return QSize(120, 32)
        
        return super().sizeHint(option, index) 