"""レシートデータの永続化と管理を担当するモジュール。ワークスペース、バックアップ、CSVエクスポートなどのデータ操作機能を提供。"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import csv

from ..utils import config, logger

class DataManager:
    """データ管理クラス"""
    
    def __init__(self):
        self._workspace: Optional[dict] = None
        self._workspace_file: Optional[Path] = None
        self._images: Dict[str, dict] = {}
        self._current_folder: Optional[Path] = None
    
    def open_folder(self, folder_path: str) -> List[dict]:
        """フォルダを開く"""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"フォルダが存在しません: {folder}")
        
        # 現在のフォルダを設定
        self._current_folder = folder
        
        # ワークスペースファイルのパスを設定
        self._workspace_file = folder / "workspace.json"
        
        # ワークスペースの読み込みまたは作成
        self._load_or_create_workspace()
        
        # 画像ファイルの読み込み
        return self._load_images()
    
    def _load_or_create_workspace(self):
        """ワークスペースの読み込みまたは作成"""
        if self._workspace_file.exists():
            try:
                with open(self._workspace_file, "r", encoding="utf-8") as f:
                    self._workspace = json.load(f)
                logger.info("既存のワークスペースを読み込みました")
            except Exception as e:
                logger.error("ワークスペースの読み込みに失敗しました", e)
                self._create_new_workspace()
        else:
            self._create_new_workspace()
    
    def _create_new_workspace(self):
        """新しいワークスペースを作成"""
        self._workspace = {
            "workspace": {
                "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "name": self._current_folder.name,
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "settings": {
                    "output_format": [
                        "Transaction Date (yyyy/mm/dd only)",
                        "Store Name",
                        "Total Amount (currency symbol removed)",
                        "The amount of consumption tax at the rate of 10%",
                        "The amount of consumption tax at the rate of 8%",
                        "The amount subject to 10% tax",
                        "The amount subject to 8% tax",
                        "Representative Item Name"
                    ]
                }
            },
            "images": {}
        }
        self._save_workspace()
        logger.info("新しいワークスペースを作成しました")
    
    def _save_workspace(self):
        """ワークスペースを保存"""
        if not self._workspace_file:
            return
        
        # バックアップの作成
        self._create_backup()
        
        # ワークスペースの保存
        try:
            self._workspace["workspace"]["last_modified"] = datetime.now().isoformat()
            with open(self._workspace_file, "w", encoding="utf-8") as f:
                json.dump(self._workspace, f, ensure_ascii=False, indent=2)
            logger.info("ワークスペースを保存しました")
        except Exception as e:
            logger.error("ワークスペースの保存に失敗しました", e)
    
    def _create_backup(self):
        """バックアップを作成"""
        if not self._workspace_file or not self._workspace_file.exists():
            return
        
        try:
            print("\n=== ワークスペースのバックアップを開始 ===")
            # バックアップディレクトリの作成（ワークスペースと同じフォルダ内に.backupjsonディレクトリを作成）
            backup_dir = self._current_folder / ".backupjson"
            backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"JSONバックアップディレクトリを作成/確認: {backup_dir}")
            
            # バックアップファイル名の生成
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_file = backup_dir / f"workspace_{timestamp}.json"
            
            # バックアップの作成
            shutil.copy2(self._workspace_file, backup_file)
            print(f"JSONバックアップを作成しました: {backup_file}")
            
            # 古いバックアップの削除
            self._cleanup_old_backups()
            
            logger.info(f"バックアップを作成しました: {backup_file}")
            print("=== ワークスペースのバックアップ完了 ===\n")
        except Exception as e:
            print(f"バックアップ作成エラー: {str(e)}")
            logger.error("バックアップの作成に失敗しました", e)
    
    def _cleanup_old_backups(self):
        """古いバックアップを削除する"""
        try:
            print("\n=== 古いバックアップの削除処理開始 ===")
            if not self._current_folder:
                print("現在のフォルダが設定されていません")
                return
                
            # 画像バックアップのクリーンアップ
            backup_image_dir = self._current_folder / ".backupimage"
            if backup_image_dir.exists():
                print("画像バックアップのクリーンアップを実行")
                self._cleanup_directory_backups(backup_image_dir, "*.*")
            
            # JSONバックアップのクリーンアップ
            backup_json_dir = self._current_folder / ".backupjson"
            if backup_json_dir.exists():
                print("JSONバックアップのクリーンアップを実行")
                self._cleanup_directory_backups(backup_json_dir, "workspace_*.json")
            
            print("=== 古いバックアップの削除処理完了 ===\n")
            
        except Exception as e:
            print(f"バックアップクリーンアップエラー: {str(e)}")
            logger.error(f"バックアップのクリーンアップに失敗しました: {e}")
    
    def _load_images(self) -> List[dict]:
        """画像ファイルの読み込み"""
        if not self._current_folder:
            return []
        
        image_data = []
        image_extensions = {".jpg", ".jpeg", ".png"}
        
        # 画像ファイルの検索
        for file in self._current_folder.glob("*"):
            if file.suffix.lower() in image_extensions:
                # JSONデータの取得または作成
                image_info = self._get_or_create_image_info(file)
                image_data.append(image_info)
        
        logger.info(f"{len(image_data)}個の画像を読み込みました")
        return image_data
    
    def _get_or_create_image_info(self, file: Path) -> dict:
        """画像情報の取得または作成"""
        relative_path = file.relative_to(self._current_folder)
        str_path = str(relative_path)
        
        # 既存のデータがあれば更新
        if str_path in self._workspace["images"]:
            image_info = self._workspace["images"][str_path]
            image_info["file_info"]["size"] = file.stat().st_size
            image_info["file_info"]["path"] = str(file.absolute())  # 絶対パスを保存
            return image_info
        
        # 新規データの作成
        image_info = {
            "file_info": {
                "path": str(file.absolute()),  # 絶対パスを保存
                "size": file.stat().st_size,
                "created_at": datetime.fromtimestamp(file.stat().st_ctime).isoformat(),
                "hash": None  # TODO: ハッシュの計算
            },
            "processing_status": {
                "status": "pending",
                "last_processed": None,
                "error_type": None,
                "error_details": None,
                "api_response_raw": None
            },
            "extracted_data": {
                "Transaction Date (yyyy/mm/dd only)": None,
                "Store Name": None,
                "Total Amount (currency symbol removed)": None,
                "The amount of consumption tax at the rate of 10%": None,
                "The amount of consumption tax at the rate of 8%": None,
                "The amount subject to 10% tax": None,
                "The amount subject to 8% tax": None,
                "Representative Item Name": None
            },
            "validation": {
                "is_valid": False,
                "errors": [],
                "warnings": []
            },
            "edit_history": []
        }
        
        # ワークスペースに追加
        self._workspace["images"][str_path] = image_info
        self._save_workspace()
        
        return image_info
    
    def update_image_status(self, image_path: str, status: str, error: Optional[Exception] = None):
        """画像の処理状態を更新"""
        if not self._workspace or image_path not in self._workspace["images"]:
            return
        
        image_info = self._workspace["images"][image_path]
        image_info["processing_status"]["status"] = status
        image_info["processing_status"]["last_processed"] = datetime.now().isoformat()
        
        if error:
            image_info["processing_status"]["error_type"] = error.__class__.__name__
            image_info["processing_status"]["error_details"] = str(error)
        else:
            image_info["processing_status"]["error_type"] = None
            image_info["processing_status"]["error_details"] = None
        
        self._save_workspace()
    
    def update_extracted_data(self, image_path: str, data: dict):
        """抽出データを更新"""
        try:
            # 絶対パスから相対パスに変換
            abs_path = Path(image_path)
            if self._current_folder:
                try:
                    rel_path = abs_path.relative_to(self._current_folder)
                    str_path = str(rel_path)
                except ValueError:
                    str_path = abs_path.name
            else:
                str_path = abs_path.name

            logger.info(f"データ更新対象: {str_path}")
            
            if not self._workspace:
                logger.error("ワークスペースが初期化されていません")
                return
            
            if str_path not in self._workspace["images"]:
                logger.error(f"指定された画像が見つかりません: {str_path}")
                return
            
            # データの更新
            image_info = self._workspace["images"][str_path]
            logger.info(f"更新前のデータ: {image_info['extracted_data']}")
            
            # 古いフィールドを削除
            old_fields = ["tax rate", "10% Tax Amount", "8% Tax Amount", "10% tax base", "8% tax base"]
            for field in old_fields:
                if field in image_info["extracted_data"]:
                    del image_info["extracted_data"][field]
            
            # 新しいデータで更新
            image_info["extracted_data"] = data
            image_info["processing_status"]["status"] = "completed"
            image_info["validation"]["is_valid"] = True
            logger.info(f"更新後のデータ: {image_info['extracted_data']}")
            
            # ワークスペースの保存
            self._save_workspace()
            logger.info(f"ワークスペースを保存しました: {str_path}")
        
        except Exception as e:
            logger.error(f"データの更新に失敗しました: {image_path}", e)
    
    def add_edit_history(self, image_path: str, field: str, old_value: Any, new_value: Any, reason: str):
        """編集履歴を追加"""
        if not self._workspace or image_path not in self._workspace["images"]:
            return
        
        image_info = self._workspace["images"][image_path]
        edit_info = {
            "timestamp": datetime.now().isoformat(),
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "edited_by": "user",
            "reason": reason
        }
        image_info["edit_history"].append(edit_info)
        
        self._save_workspace()
    
    def export_csv(self, output_path: str):
        """抽出データをCSVファイルとしてエクスポート"""
        if not self._workspace:
            logger.error("ワークスペースが初期化されていません")
            return
            
        try:
            # ヘッダーの取得（設定された出力フォーマット）
            headers = self._workspace["workspace"]["settings"]["output_format"]
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                # 各画像の抽出データを書き出し
                for image_info in self._workspace["images"].values():
                    if "extracted_data" in image_info:
                        writer.writerow(image_info["extracted_data"])
            
            logger.info(f"CSVファイルを出力しました: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"CSVファイルの出力に失敗しました: {str(e)}")
            return False
    
    def export_json(self, output_path: str):
        """JSONファイルにエクスポート"""
        if not self._workspace:
            return
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self._workspace, f, ensure_ascii=False, indent=2)
            logger.info(f"JSONファイルをエクスポートしました: {output_path}")
        except Exception as e:
            logger.error("JSONファイルのエクスポートに失敗しました", e)

    def rename_image(self, image_info: dict) -> bool:
        """画像ファイルのリネーム処理"""
        try:
            print("\n=== リネーム処理開始 ===")
            # 必要なデータの取得
            extracted_data = image_info["extracted_data"]
            
            # データが未抽出の場合はスキップ
            if not self._can_rename(extracted_data):
                print("必要なデータが未抽出のため、リネームをスキップします")
                logger.info("必要なデータが未抽出のため、リネームをスキップします")
                return False

            # 新しいファイル名の生成
            old_path = Path(image_info["file_info"]["path"])
            new_name = self._generate_filename(extracted_data, old_path.suffix)
            new_path = old_path.parent / new_name
            print(f"現在のパス: {old_path}")
            print(f"新しいパス: {new_path}")

            # 重複チェックと解決
            new_path = self._resolve_filename_conflict(new_path)
            if new_path != old_path.parent / new_name:
                print(f"ファイル名が重複したため、変更されました: {new_path}")

            # バックアップの作成
            backup_path = self._backup_image(old_path)
            if not backup_path:
                print("バックアップの作成に失敗したため、リネームを中止します")
                logger.warning("バックアップの作成に失敗したため、リネームを中止します")
                return False

            print("ワークスペースのJSONを更新します")
            # ワークスペースのJSONを更新
            old_relative_path = str(old_path.relative_to(self._current_folder))
            new_relative_path = str(new_path.relative_to(self._current_folder))

            # JSONのキーを更新
            if old_relative_path in self._workspace["images"]:
                self._workspace["images"][new_relative_path] = self._workspace["images"].pop(old_relative_path)
                # パス情報も更新
                self._workspace["images"][new_relative_path]["file_info"]["path"] = str(new_path)
                print("JSONの更新が完了しました")

            # リネーム実行
            print(f"ファイルをリネームします: {old_path} -> {new_path}")
            old_path.rename(new_path)

            # image_infoの更新（UIの表示用）
            image_info["file_info"]["path"] = str(new_path)

            # ワークスペースの保存
            self._save_workspace()
            print("ワークスペースを保存しました")

            logger.info(f"ファイルをリネームしました: {old_path} -> {new_path}")
            print("=== リネーム処理完了 ===\n")
            return True

        except Exception as e:
            print(f"リネーム処理エラー: {str(e)}")
            logger.error(f"リネーム処理に失敗しました: {e}")
            return False

    def _can_rename(self, extracted_data: dict) -> bool:
        """リネームに必要なデータが揃っているかチェック"""
        required_fields = ["Transaction Date (yyyy/mm/dd only)", "Store Name"]
        return all(extracted_data.get(field) is not None for field in required_fields)

    def _generate_filename(self, extracted_data: dict, suffix: str) -> str:
        """ファイル名の生成"""
        date = extracted_data.get("Transaction Date (yyyy/mm/dd only)", "")
        store = extracted_data.get("Store Name", "")
        
        # 不正なファイル名文字を置換
        store = "".join(c if c.isalnum() or c in "._- " else "_" for c in store)
        
        # 日付をフォーマット（YYYY-MM-DD形式に変換）
        if date:
            try:
                date = date.replace("/", "-")
            except:
                pass
        
        # ファイル名生成
        filename = f"{date}_{store}{suffix}"
        return filename

    def _resolve_filename_conflict(self, path: Path) -> Path:
        """ファイル名の重複を解決"""
        if not path.exists():
            return path

        base = path.stem
        suffix = path.suffix
        counter = 1
        
        while True:
            new_path = path.parent / f"{base}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def _backup_image(self, image_path: Path) -> Optional[Path]:
        """画像ファイルのバックアップを作成する
        
        Args:
            image_path (Path): バックアップする画像のパス
        
        Returns:
            Optional[Path]: バックアップファイルのパス。失敗した場合はNone
        """
        try:
            print(f"\n=== 画像バックアップを開始: {image_path} ===")
            # バックアップディレクトリの作成（画像と同じフォルダ内に.backupimageディレクトリを作成）
            backup_dir = image_path.parent / ".backupimage"
            backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"画像バックアップディレクトリを作成/確認: {backup_dir}")
            
            # バックアップファイル名の生成
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_path = backup_dir / f"{timestamp}_{image_path.name}"
            
            # ファイルのコピー
            shutil.copy2(image_path, backup_path)
            print(f"画像バックアップを作成しました: {backup_path}")
            
            logger.info(f"画像のバックアップを作成しました: {backup_path}")
            print("=== 画像バックアップ完了 ===\n")
            
            return backup_path
        
        except Exception as e:
            print(f"画像バックアップ作成エラー: {str(e)}")
            logger.error(f"画像のバックアップ作成に失敗しました: {e}")
            return None

    def _cleanup_directory_backups(self, directory: Path, pattern: str):
        """指定ディレクトリの古いバックアップを削除する"""
        if not directory.exists():
            return
            
        print(f"\n=== バックアップクリーンアップ開始: {directory} ===")
        print(f"検索パターン: {pattern}")
        
        # 画像バックアップの場合は、元のファイル名ごとに最新のバックアップのみを保持
        if ".backupimage" in str(directory):
            # バックアップファイルの一覧を取得
            backups = list(directory.glob(pattern))
            print(f"バックアップファイル数: {len(backups)}")
            
            # バックアップファイルを元のファイル名でグループ化
            backup_groups = {}
            for backup in backups:
                # タイムスタンプを除いた元のファイル名を取得
                original_name = "_".join(backup.name.split("_")[1:])
                if original_name not in backup_groups:
                    backup_groups[original_name] = []
                backup_groups[original_name].append(backup)
            
            # 各グループで最新のファイル以外を削除
            for original_name, group_backups in backup_groups.items():
                if len(group_backups) > 1:
                    # 更新日時でソート
                    sorted_backups = sorted(
                        group_backups,
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    # 最新以外を削除
                    for backup in sorted_backups[1:]:
                        print(f"古いバックアップを削除: {backup}")
                        backup.unlink()
                        logger.debug(f"古いバックアップを削除しました: {backup}")
        
        # JSONバックアップの場合は従来通りの世代管理
        else:
            # バックアップファイルの一覧を取得
            backups = sorted(
                directory.glob(pattern),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # 設定された世代数を超えるバックアップを削除
            max_generations = config.get("backup.generations", 3)
            print(f"保持する最大世代数: {max_generations}")
            print(f"現在のバックアップ数: {len(backups)}")
            
            for backup in backups[max_generations:]:
                print(f"古いバックアップを削除: {backup}")
                backup.unlink()
                logger.debug(f"古いバックアップを削除しました: {backup}")
        
        print("=== バックアップクリーンアップ完了 ===\n")

# シングルトンインスタンス
data_manager = DataManager() 