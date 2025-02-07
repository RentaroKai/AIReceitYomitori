import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    """設定管理クラス"""
    
    def __init__(self):
        self._config_dir = Path.home() / ".ai_receipt_extractor"
        self._config_file = self._config_dir / "config.json"
        self._config: Dict[str, Any] = {}
        
        # 設定ディレクトリの作成
        self._config_dir.mkdir(parents=True, exist_ok=True)
        
        # デフォルト設定の読み込み
        self._load_defaults()
        
        # 保存された設定の読み込み（存在する場合）
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    self._update_recursive(self._config, saved_config)
            except Exception as e:
                logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
    
    def _load_defaults(self):
        """デフォルト設定の読み込み"""
        self._config = {
            "backup": {
                "generations": 3,
                "max_generations": 10,
                "min_generations": 3,
                "directory": str(self._config_dir / "backups")
            },
            "api": {
                "timeout": 30,
                "key": None
            },
            "ui": {
                "font_size": 10,
                "theme": "light",
                "language": "ja",
                "table": {
                    "visible_columns": [
                        "checkbox",
                        "status",
                        "preview",
                        "filename",
                        "store",
                        "date",
                        "amount",
                        "process_status",
                        "actions"
                    ],
                    "column_order": None,
                    "sort_column": "filename",
                    "sort_order": "ascending"
                }
            },
            "processing": {
                "image": {
                    "resize": {
                        "enabled": True,
                        "max_width": 1920,
                        "max_height": 1080,
                        "quality": 85
                    }
                }
            },
            "rename": {
                "format": "{date}_{store}",
                "date_format": "YYYY-MM-DD",
                "separator": "_",
                "duplicate_action": "add_number"
            },
            "folders": {
                "default_path": None,  # デフォルトフォルダパスの設定
                "remember_last": True  # 最後に使用したフォルダを記憶するかどうか
            },
            "recent_folders": []
        }
    
    def load(self):
        """設定ファイルから設定を読み込む"""
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    # デフォルト設定を読み込んでから保存された設定で上書き
                    self._load_defaults()
                    self._update_recursive(self._config, saved_config)
            else:
                # 設定ファイルが存在しない場合はデフォルト設定を読み込む
                self._load_defaults()
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            # エラーが発生した場合はデフォルト設定を使用
            self._load_defaults()
    
    def save(self):
        """設定をファイルに保存する"""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")
    
    def _update_recursive(self, base: Dict, update: Dict):
        """辞書を再帰的に更新する"""
        for key, value in update.items():
            if key in base:
                if isinstance(value, dict) and isinstance(base[key], dict):
                    self._update_recursive(base[key], value)
                else:
                    base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得する"""
        try:
            keys = key.split(".")
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """設定値を設定する"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def add_recent_folder(self, folder: str):
        """最近使用したフォルダを追加する"""
        recent = self.get("recent_folders", [])
        if folder in recent:
            recent.remove(folder)
        recent.insert(0, folder)
        recent = recent[:10]  # 最大10件まで保持
        self.set("recent_folders", recent)

# シングルトンインスタンス
config = Config() 