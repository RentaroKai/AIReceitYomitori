"""アプリケーションのメインウィンドウを実装するモジュール。UIの中心的な制御とユーザーインタラクションを管理。"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QMenuBar, QStatusBar,
    QToolBar, QFileDialog, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QAction, QIcon
from typing import Optional
import os
from pathlib import Path

from src.ui.widgets import ImageTableView
from src.ui.dialogs import APIKeyDialog, SettingsDialog, EditDialog, ManualDialog
from src.ui.dialogs.processing_dialog import ProcessingDialog
from src.core import data_manager, image_processor
from src.utils import config, logger
from .dialogs.log_viewer_dialog import LogViewerDialog

class ImageProcessThread(QThread):
    """画像処理スレッド"""
    
    # シグナル定義
    progress = Signal(int, int)  # 進捗状況（現在の処理数、合計数）
    error = Signal(str, str)  # エラー（画像パス、エラーメッセージ）
    api_error = Signal(str)  # APIエラー（エラーメッセージ）
    finished = Signal()  # 完了
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_cancelled = False
    
    def run(self):
        """処理を実行"""
        print("\n=== 処理スレッド開始 ===")
        try:
            # バッチ処理を実行
            print("バッチ処理を開始します")
            if not image_processor.process_queue():
                print("処理を開始できませんでした")
                self.error.emit("", "処理を開始できませんでした")
                return
            
            # 処理の進捗を監視
            while image_processor.is_processing() and not self._is_cancelled:
                if self._is_cancelled:
                    print("処理がキャンセルされました")
                    break
                
                current, total = image_processor.get_progress()
                self.progress.emit(current, total)
                print(f"処理進捗: {current}/{total}")
                self.msleep(100)  # 進捗更新の間隔
            
            if self._is_cancelled:
                print("処理が中断されました")
                image_processor.clear_queue()
        
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            logger.error("画像処理スレッドでエラーが発生しました", str(e))
            error_message = str(e)
            
            # エラーメッセージを解析
            if ":" in error_message:
                error_type, message = error_message.split(":", 1)
                message = message.strip()
                
                # APIエラーの場合
                if error_type in ["INVALID_API_KEY", "MISSING_API_KEY", "QUOTA_EXCEEDED"]:
                    print(f"APIエラーを検出: {error_type}")
                    print(f"エラーメッセージ: {message}")
                    self.api_error.emit(message)
                # その他のエラーの場合
                else:
                    print(f"一般エラーを検出: {error_type}")
                    self.error.emit("", message)
            # エラータイプが不明な場合
            else:
                print("未分類のエラーを検出")
                self.error.emit("", error_message)
        
        finally:
            print("=== 処理スレッド終了 ===")
            self.finished.emit()
    
    def cancel(self):
        """処理をキャンセル"""
        print("キャンセルが要求されました")
        self._is_cancelled = True
        image_processor.clear_queue()

class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウの基本設定
        self.setWindowTitle("AI Receipt Extractor")
        self.setMinimumSize(QSize(800, 600))
        
        # 最近使用したフォルダの読み込み
        self._recent_folders = config.get("recent_folders", [])
        
        # 中央ウィジェットの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # テーブルビューの設定
        self.table_view = ImageTableView()
        self.layout.addWidget(self.table_view)
        
        # UI要素の初期化
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # 処理スレッド
        self._process_thread: Optional[ImageProcessThread] = None
        
        # シグナルの接続
        self._connect_signals()
        
        # 設定の適用
        self._apply_settings()
        
        logger.info("メインウィンドウを初期化しました")
    
    def _connect_signals(self):
        """シグナルの接続"""
        # テーブルビューのシグナル
        self.table_view.reprocess_requested.connect(self._on_reprocess_requested)
        self.table_view.edit_requested.connect(self._on_edit_requested)
    
    def _setup_menubar(self):
        """メニューバーの設定"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        # フォルダを開く
        open_action = QAction("フォルダを開く...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_folder)
        file_menu.addAction(open_action)
        
        # 最近使用したフォルダ
        self.recent_menu = file_menu.addMenu("最近使用したフォルダ")
        self._update_recent_menu()
        
        file_menu.addSeparator()
        
        # エクスポート
        export_menu = file_menu.addMenu("エクスポート")
        export_csv_action = QAction("CSV形式でエクスポート...", self)
        export_json_action = QAction("JSON形式でエクスポート...", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        export_json_action.triggered.connect(self._on_export_json)
        export_menu.addAction(export_csv_action)
        export_menu.addAction(export_json_action)
        
        file_menu.addSeparator()
        
        # 終了
        exit_action = QAction("終了", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 編集メニュー
        edit_menu = menubar.addMenu("編集")
        
        # 選択
        select_all_action = QAction("すべて選択", self)
        select_none_action = QAction("選択解除", self)
        select_all_action.triggered.connect(self.table_view.check_all)
        select_none_action.triggered.connect(self.table_view.uncheck_all)
        edit_menu.addAction(select_all_action)
        edit_menu.addAction(select_none_action)
        
        edit_menu.addSeparator()
        
        # 処理
        process_action = QAction("選択項目の処理", self)
        rename_action = QAction("選択項目のリネーム", self)
        process_action.triggered.connect(self._on_process_selected)
        rename_action.triggered.connect(self._on_rename_selected)
        edit_menu.addAction(process_action)
        edit_menu.addAction(rename_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu("表示")
        
        # 列の表示/非表示
        columns_menu = view_menu.addMenu("列の表示/非表示")
        for column in self.table_view._model.COLUMNS:
            if column["id"] not in ["checkbox", "actions", "process_status"]:
                action = QAction(column["name"], self)
                action.setCheckable(True)
                action.setChecked(True)
                action.triggered.connect(
                    lambda checked, col=column["id"]: self.table_view.set_column_visible(col, checked)
                )
                columns_menu.addAction(action)
        
        # ログビューワー
        log_viewer_action = QAction("ログビューワー...", self)
        log_viewer_action.triggered.connect(self._show_log_viewer)
        view_menu.addAction(log_viewer_action)
        
        # ツールメニュー
        tools_menu = menubar.addMenu("ツール")
        
        # 設定
        settings_action = QAction("設定...", self)
        api_settings_action = QAction("APIキー設定...", self)
        settings_action.triggered.connect(self._on_settings)
        api_settings_action.triggered.connect(self._on_api_settings)
        tools_menu.addAction(settings_action)
        tools_menu.addAction(api_settings_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        
        # マニュアル
        manual_action = QAction("マニュアル", self)
        manual_action.triggered.connect(self._show_manual)
        help_menu.addAction(manual_action)
    
    def _setup_toolbar(self):
        """ツールバーの設定"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 現在の画像フォルダを開く
        open_folder_action = QAction("フォルダを開く", self)
        open_folder_action.setIcon(QIcon.fromTheme("folder-open", QIcon(":/icons/folder")))  # システムアイコンを使用
        open_folder_action.setText("📁 フォルダを開く")
        open_folder_action.setToolTip("現在選択中の画像があるフォルダを開く")
        open_folder_action.triggered.connect(self._open_current_image_folder)
        toolbar.addAction(open_folder_action)
        
        toolbar.addSeparator()
        
        # 処理実行
        process_action = QAction("読み取り処理実行", self)
        process_action.setObjectName("process_action")  # オブジェクト名を設定
        process_action.triggered.connect(self._on_process_selected)
        toolbar.addAction(process_action)
        
        # リネーム実行
        rename_action = QAction("リネーム", self)
        rename_action.setObjectName("rename_action")  # オブジェクト名を設定
        rename_action.triggered.connect(self._on_rename_selected)
        toolbar.addAction(rename_action)
        
        # 設定とヘルプは上段メニューバーのみに表示
        # toolbar.addSeparator()
        # settings_action = QAction("設定", self)
        # toolbar.addAction(settings_action)
    
    def _setup_statusbar(self):
        """ステータスバーの設定"""
        self.statusBar().showMessage("準備完了")
    
    def _on_open_folder(self):
        """フォルダを開くダイアログを表示"""
        # デフォルトパスの取得
        folder_config = config.get("folders", {})
        default_path = None

        # 最後に使用したフォルダを記憶する設定の場合
        if folder_config.get("remember_last", True) and self._recent_folders:
            default_path = self._recent_folders[0]
        # デフォルトフォルダパスが設定されている場合
        elif folder_config.get("default_path"):
            default_path = folder_config.get("default_path")

        folder = QFileDialog.getExistingDirectory(
            self,
            "画像フォルダの選択",
            default_path or ""
        )
        
        if folder:
            self._open_folder(folder)
    
    def _open_folder(self, folder: str):
        """フォルダを開く"""
        logger.info(f"フォルダを開きます: {folder}")
        
        try:
            # データマネージャーでフォルダを開く
            image_data = data_manager.open_folder(folder)
            
            # 最近使用したフォルダに追加
            config.add_recent_folder(folder)
            self._update_recent_menu()
            
            # テーブルビューをクリア
            self.table_view.clear()
            
            # 画像データをテーブルビューに追加
            for data in image_data:
                self.table_view.add_image(data)
            
            self.statusBar().showMessage(f"{len(image_data)}個の画像を読み込みました")
        except Exception as e:
            logger.error("フォルダを開けませんでした", e)
            QMessageBox.critical(
                self,
                "エラー",
                f"フォルダを開けませんでした：\n{str(e)}"
            )
    
    def _update_recent_menu(self):
        """最近使用したフォルダメニューを更新"""
        self.recent_menu.clear()
        
        for folder in self._recent_folders:
            action = QAction(folder, self)
            action.triggered.connect(lambda checked, folder=folder: self._open_folder(folder))
            self.recent_menu.addAction(action)
        
        if self._recent_folders:
            self.recent_menu.addSeparator()
            clear_action = QAction("履歴をクリア", self)
            clear_action.triggered.connect(self._clear_recent_folders)
            self.recent_menu.addAction(clear_action)
    
    def _clear_recent_folders(self):
        """最近使用したフォルダの履歴をクリア"""
        self._recent_folders = []
        config.set("recent_folders", [])
        self._update_recent_menu()
    
    def _on_process_selected(self):
        """選択された画像の処理を実行"""
        # 選択された画像を取得
        selected_items = self.table_view.get_checked_items()
        if not selected_items:
            QMessageBox.warning(self, "警告", "処理する画像が選択されていません。")
            return

        # 処理中なら中断
        if image_processor.is_processing():
            image_processor.clear_queue()
            self.statusBar().showMessage("処理をキャンセルしました")
            return

        # 処理ダイアログを表示
        self._progress_dialog = ProcessingDialog(self)
        self._progress_dialog.cancelled.connect(self._on_process_cancelled)

        # 処理スレッドの設定
        self._process_thread = ImageProcessThread(self)
        self._process_thread.progress.connect(lambda current, total: print(f"Progress: {current}/{total}"))
        self._process_thread.error.connect(self._on_process_error)
        self._process_thread.api_error.connect(self._on_api_error)
        self._process_thread.finished.connect(self._on_process_finished)
        self._process_thread.finished.connect(self._progress_dialog.accept)

        # 処理キューに追加
        image_paths = [item["file_info"]["path"] for item in selected_items]
        image_processor.add_to_queue(image_paths)

        # 処理を開始
        self._process_thread.start()
        self._progress_dialog.exec()

    def _on_process_error(self, image_path: str, error_message: str):
        """処理エラーの処理"""
        logger.error(f"画像の処理でエラーが発生しました: {image_path}: {error_message}")
        self.statusBar().showMessage(f"エラー: {error_message}")
    
    def _on_process_finished(self):
        """処理完了の処理"""
        # 処理ダイアログを自動クローズに設定して閉じる
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.set_auto_close(True)
            self._progress_dialog.close()
        
        if self._process_thread and not self._process_thread._is_cancelled:
            self.statusBar().showMessage("処理が完了しました")
        
        # スレッドの終了を待機
        if self._process_thread:
            self._process_thread.wait()
        
        # テーブルビューの更新
        self.table_view.viewport().update()
    
    def _on_rename_selected(self):
        """選択項目のリネーム"""
        items = self.table_view.get_checked_items()
        if not items:
            self.statusBar().showMessage("リネームする項目が選択されていません")
            return

        # リネーム処理の実行
        success_count = 0
        skip_count = 0
        error_count = 0

        for item in items:
            try:
                result = data_manager.rename_image(item)
                if result:
                    success_count += 1
                else:
                    skip_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"リネーム処理でエラーが発生しました: {e}")

        # 結果の表示
        message = f"リネーム完了: 成功 {success_count}件"
        if skip_count > 0:
            message += f", スキップ {skip_count}件"
        if error_count > 0:
            message += f", エラー {error_count}件"
        self.statusBar().showMessage(message)

        # テーブルビューの更新
        self.table_view.viewport().update()
    
    def _on_reprocess_requested(self, item: dict):
        """再処理リクエスト"""
        try:
            image_path = item["file_info"]["path"]
            image_processor.process_image(image_path)
            self.statusBar().showMessage("再処理が完了しました")
            
            # テーブルビューの更新
            self.table_view.viewport().update()
        
        except Exception as e:
            logger.error("再処理に失敗しました", e)
            error_message = str(e)
            if ":" in error_message:
                error_type, message = error_message.split(":", 1)
                if error_type in ["INVALID_API_KEY", "MISSING_API_KEY", "QUOTA_EXCEEDED"]:
                    QMessageBox.warning(self, "APIエラー", message)
                else:
                    QMessageBox.critical(self, "エラー", f"再処理に失敗しました：\n{message}")
            else:
                QMessageBox.critical(self, "エラー", f"再処理に失敗しました：\n{error_message}")
    
    def _on_edit_requested(self, item: dict):
        """編集リクエスト"""
        dialog = EditDialog(self, item)
        if dialog.exec():
            # 編集後にテーブルビューを更新
            self.table_view.viewport().update()
            self.statusBar().showMessage("データを更新しました")
    
    def _on_export_csv(self):
        """CSVエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "CSVファイルの保存",
            "",
            "CSV files (*.csv)"
        )
        
        if file_path:
            try:
                data_manager.export_csv(file_path)
                self.statusBar().showMessage("CSVファイルをエクスポートしました")
            except Exception as e:
                logger.error("CSVファイルのエクスポートに失敗しました", e)
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"CSVファイルのエクスポートに失敗しました：\n{str(e)}"
                )
    
    def _on_export_json(self):
        """JSONエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "JSONファイルの保存",
            "",
            "JSON files (*.json)"
        )
        
        if file_path:
            try:
                data_manager.export_json(file_path)
                self.statusBar().showMessage("JSONファイルをエクスポートしました")
            except Exception as e:
                logger.error("JSONファイルのエクスポートに失敗しました", e)
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"JSONファイルのエクスポートに失敗しました：\n{str(e)}"
                )
    
    def _on_settings(self):
        """設定ダイアログを表示"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # 設定の適用
            self._apply_settings()
        return dialog

    def _apply_settings(self):
        """保存された設定を適用"""
        # フォントサイズの適用
        self._apply_font_size(config.get("ui.font_size", 10))
        
        # テーマの適用
        theme = config.get("ui.theme", "light")
        self._apply_theme(theme)
    
    def _apply_font_size(self, size: int):
        """フォントサイズを適用"""
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        self.table_view.setFont(font)
        self.menuBar().setFont(font)
        self.statusBar().setFont(font)
    
    def _on_api_settings(self):
        """APIキー設定ダイアログを表示"""
        dialog = APIKeyDialog(self)
        if dialog.exec():
            # APIキー設定後にGemini APIを再初期化
            image_processor._setup_gemini()

    def _open_current_image_folder(self):
        """テーブルの一番上にある画像のフォルダを開く"""
        # テーブルに画像があるか確認
        if not self.table_view._model._data:
            self.statusBar().showMessage("画像がありません")
            return
            
        # 一番上の画像データを取得
        image_data = self.table_view._model._data[0]
        image_path = image_data.get("file_info", {}).get("path")
        
        if not image_path:
            self.statusBar().showMessage("画像のパスが見つかりません")
            return
            
        # フォルダを開く
        try:
            folder_path = str(Path(image_path).parent)
            os.startfile(folder_path)
            self.statusBar().showMessage(f"フォルダを開きました: {folder_path}")
        except Exception as e:
            logger.error("フォルダを開けませんでした", e)
            QMessageBox.critical(
                self,
                "エラー",
                f"フォルダを開けませんでした：\n{str(e)}"
            )

    def _show_manual(self):
        """マニュアルダイアログを表示"""
        dialog = ManualDialog(self)
        dialog.exec()

    def _show_log_viewer(self):
        """ログビューワーダイアログを表示"""
        dialog = LogViewerDialog(self)
        dialog.exec()

    def _apply_theme(self, theme: str):
        """テーマを適用"""
        if theme == "dark":
            # ダークテーマのスタイルシートを適用
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #3c3f41;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #3c3f41;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #4b6eaf;
                }
            """)
        else:
            # ライトテーマ（デフォルト）
            self.setStyleSheet("") 

    def _on_api_error(self, error_message: str):
        """APIエラーの処理"""
        logger.error(f"APIエラーが発生しました: {error_message}")
        # 処理ダイアログを自動クローズに設定して閉じる
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.set_auto_close(True)
            self._progress_dialog.close()
        # エラーダイアログを表示
        QMessageBox.warning(self, "APIエラー", error_message)
        self.statusBar().showMessage(f"APIエラー: {error_message}")

    def _on_process_cancelled(self):
        """処理がキャンセルされた時の処理"""
        if self._process_thread and self._process_thread.isRunning():
            print("処理をキャンセルします...")
            self._process_thread.cancel() 