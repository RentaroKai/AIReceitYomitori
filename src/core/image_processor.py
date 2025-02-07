import os
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

from src.utils import config, logger
from src.core.data_manager import data_manager

class ImageProcessor:
    """画像処理クラス"""
    
    def __init__(self):
        self._setup_gemini()
        self._processing_queue = []
        self._is_processing = False
        self._current_progress = 0
        self._total_items = 0
    
    def add_to_queue(self, image_paths: list):
        """処理キューに画像を追加"""
        self._processing_queue.extend(image_paths)
        logger.info(f"{len(image_paths)}個の画像を処理キューに追加しました")
    
    def clear_queue(self):
        """処理キューをクリア"""
        self._processing_queue.clear()
        logger.info("処理キューをクリアしました")
    
    def is_processing(self) -> bool:
        """処理中かどうかを返す"""
        return self._is_processing
    
    def process_queue(self) -> bool:
        """キューの画像を処理"""
        if self._is_processing:
            logger.warning("既に処理が実行中です")
            return False
        
        if not self._processing_queue:
            logger.warning("処理キューが空です")
            return False
        
        if not hasattr(self, '_model'):
            logger.error("Gemini APIが初期化されていません")
            return False
        
        try:
            self._is_processing = True
            self._total_items = len(self._processing_queue)
            self._current_progress = 0
            
            logger.info(f"バッチ処理を開始します: 合計{self._total_items}個の画像")
            
            for image_path in self._processing_queue[:]:
                try:
                    # 処理状態を更新
                    data_manager.update_image_status(image_path, "processing")
                    logger.info(f"画像を処理中: {image_path}")
                    
                    # 画像を処理
                    result = self.process_image(image_path)
                    
                    # 処理結果を保存
                    data_manager.update_extracted_data(image_path, result)
                    logger.info(f"画像の処理が完了しました: {image_path}")
                    
                    # キューから削除
                    self._processing_queue.remove(image_path)
                    
                    # 進捗を更新
                    self._current_progress += 1
                    
                except Exception as e:
                    logger.error(f"画像の処理でエラーが発生しました: {image_path}", e)
                    data_manager.update_image_status(image_path, "error", e)
                    # エラーが発生しても処理を継続
                    continue
            
            logger.info("バッチ処理が完了しました")
            return True
        
        finally:
            self._is_processing = False
            self._processing_queue.clear()
            self._current_progress = 0
            self._total_items = 0
    
    def get_progress(self) -> tuple:
        """現在の進捗状況を取得"""
        return self._current_progress, self._total_items
    
    def _setup_gemini(self):
        """Gemini APIの設定"""
        try:
            # APIキーの取得（環境変数 > クレデンシャルマネージャー > 設定）
            api_key = os.getenv("GOOGLE_API_KEY")
            logger.info(f"環境変数からのAPIキー取得: {'成功' if api_key else '失敗'}")
            
            if not api_key:
                # TODO: クレデンシャルマネージャーからの取得
                api_key = config.get("api.key")
                logger.info(f"設定からのAPIキー取得: {'成功' if api_key else '失敗'}")
            
            if not api_key:
                logger.error("Gemini APIキーが設定されていません")
                return
            
            # Gemini APIの初期化
            genai.configure(api_key=api_key)
            
            # 生成設定
            self._generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_schema": content.Schema(
                    type=content.Type.OBJECT,
                    enum=[],
                    required=["Transaction Date (yyyy/mm/dd only)", "Store Name", "Total Amount (currency symbol removed)"],
                    properties={
                        "Transaction Date (yyyy/mm/dd only)": content.Schema(
                            type=content.Type.STRING,
                        ),
                        "Store Name": content.Schema(
                            type=content.Type.STRING,
                        ),
                        "Total Amount (currency symbol removed)": content.Schema(
                            type=content.Type.INTEGER,
                        ),
                        "The amount of consumption tax at the rate of 10%": content.Schema(
                            type=content.Type.INTEGER,
                        ),
                        "The amount of consumption tax at the rate of 8%": content.Schema(
                            type=content.Type.INTEGER,
                        ),
                        "The amount subject to 10% tax": content.Schema(
                            type=content.Type.INTEGER,
                        ),
                        "The amount subject to 8% tax": content.Schema(
                            type=content.Type.INTEGER,
                        )
                    },
                ),
                "response_mime_type": "application/json",
            }
            
            # Geminiモデルの作成
            self._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config=self._generation_config
            )
            
            # システムプロンプトを設定
            self._model.system_instruction = (
                "Extract the following textual information from the image:\n"
                "- Transaction date (yyyy/mm/dd only, without time)\n"
                "- Store name\n"
                "- Total amount (currency symbols removed)\n"
                "- tax rate /tax amount/tax base\n"
                "Output in JSON format."
            )
            
            logger.info("Gemini APIを初期化しました")
        
        except Exception as e:
            logger.error("Gemini APIの初期化に失敗しました", e)
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """画像を処理する"""
        if not hasattr(self, '_model'):
            raise RuntimeError("Gemini APIが初期化されていません")
        
        try:
            # 画像の前処理
            processed_path = self._preprocess_image(image_path)
            
            # Gemini APIで画像を処理
            result = self._process_with_gemini(processed_path)
            
            # 処理結果を保存
            data_manager.update_extracted_data(image_path, result)
            
            return result
        
        except Exception as e:
            # エラー情報を保存
            data_manager.update_image_status(image_path, "error", e)
            raise
    
    def _preprocess_image(self, image_path: str) -> str:
        """画像の前処理を行う"""
        try:
            # 画像を開く
            image = Image.open(image_path)
            original_size = image.size
            logger.info(f"元の画像サイズ: {original_size}")
            
            # リサイズ設定の取得
            resize_config = config.get("processing.image.resize", {})
            if resize_config.get("enabled", True):
                # 最大サイズを取得
                max_width = resize_config.get("max_width", 1920)
                max_height = resize_config.get("max_height", 1080)
                
                # 現在のサイズが最大サイズを超えている場合のみリサイズ
                if original_size[0] > max_width or original_size[1] > max_height:
                    # アスペクト比を保持してリサイズ
                    ratio = min(max_width/original_size[0], max_height/original_size[1])
                    new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(f"画像をリサイズしました: {new_size}")
                else:
                    logger.info("リサイズは不要です（元のサイズが最大サイズ以下）")
            
            # 一時ファイルとして保存
            temp_dir = Path(config.get("backup.directory", "")).parent / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"一時ディレクトリを作成/確認: {temp_dir}")
            
            output_path = temp_dir / f"processed_{Path(image_path).name}"
            image.save(
                output_path,
                quality=resize_config.get("quality", 85),
                optimize=True
            )
            logger.info(f"処理済み画像を保存: {output_path}")
            
            return str(output_path)
        
        except Exception as e:
            logger.error(f"画像の前処理に失敗しました: {e}")
            raise
    
    def _process_with_gemini(self, image_path: str) -> Dict[str, Any]:
        """Gemini APIで画像を処理する"""
        try:
            # 画像をアップロード
            image = genai.upload_file(image_path, mime_type="image/jpeg")
            logger.info(f"画像をアップロードしました: {image.display_name}")
            
            # チャットセッションを開始
            response = self._model.generate_content(
                [image, "解析せよ"]
            )
            
            # レスポンスを解析
            if response.text:
                # JSON文字列から余分な部分を削除
                json_str = response.text.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                
                logger.info(f"APIレスポンス: {json_str}")
                
                # JSON文字列をディクショナリに変換
                import json
                result = json.loads(json_str)
                
                # フィールド名の変換マッピング
                field_mapping = {
                    "10% Tax Amount": "The amount of consumption tax at the rate of 10%",
                    "8% Tax Amount": "The amount of consumption tax at the rate of 8%",
                    "10% tax base": "The amount subject to 10% tax",
                    "8% tax base": "The amount subject to 8% tax"
                }
                
                # フィールド名を変換
                converted_result = {}
                for key, value in result.items():
                    new_key = field_mapping.get(key, key)
                    converted_result[new_key] = value
                
                # 不足しているフィールドにNoneを設定
                required_fields = [
                    "Transaction Date (yyyy/mm/dd only)",
                    "Store Name",
                    "Total Amount (currency symbol removed)",
                    "The amount of consumption tax at the rate of 10%",
                    "The amount of consumption tax at the rate of 8%",
                    "The amount subject to 10% tax",
                    "The amount subject to 8% tax"
                ]
                for field in required_fields:
                    if field not in converted_result:
                        converted_result[field] = None
                
                logger.info(f"変換後のデータ: {converted_result}")
                return converted_result
            
            raise RuntimeError("Gemini APIからの応答が空です")
        
        except Exception as e:
            logger.error("Gemini APIでの処理に失敗しました", e)
            raise

# シングルトンインスタンス
image_processor = ImageProcessor() 