"""テーブルヘッダーのカスタマイズを行うモジュール。チェックボックスやソート機能を含むヘッダーを実装。"""

from PySide6.QtWidgets import QHeaderView, QStyleOptionButton, QStyle
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter

class CustomHeaderView(QHeaderView):
    """カスタムヘッダービュー"""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        
    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int):
        """セクションの描画"""
        if logical_index == 0:  # チェックボックス列
            option = QStyleOptionButton()
            option.rect = QRect(rect.left() + rect.width() // 4, 
                              rect.top() + rect.height() // 4,
                              rect.width() // 2, 
                              rect.height() // 2)
            
            # チェックボックスの状態を取得
            if self.model():
                check_state = self.model().headerData(0, Qt.Horizontal, Qt.CheckStateRole)
                if check_state == Qt.Checked:
                    option.state = QStyle.State_Enabled | QStyle.State_Active | QStyle.State_On
                else:
                    option.state = QStyle.State_Enabled | QStyle.State_Active
            
            # チェックボックスを描画
            self.style().drawControl(QStyle.CE_CheckBox, option, painter, self)
        else:
            # 他の列は通常通り描画
            super().paintSection(painter, rect, logical_index)
    
    def mousePressEvent(self, event):
        """マウスクリックイベント"""
        index = self.logicalIndexAt(event.pos())
        
        if index == 0:  # チェックボックス列
            # チェックボックスの領域内かどうかを確認
            rect = self.rect()
            check_rect = QRect(rect.left() + rect.width() // 4,
                             rect.top() + rect.height() // 4,
                             rect.width() // 2,
                             rect.height() // 2)
            
            if check_rect.contains(event.pos()):
                # チェックボックスの状態を切り替え
                self.sectionClicked.emit(0)
                return
                
        # 他の列は通常通り処理
        super().mousePressEvent(event) 