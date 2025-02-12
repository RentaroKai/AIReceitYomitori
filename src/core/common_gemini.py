"""Gemini APIで使用する画像処理の共通機能を提供するモジュール。画像の前処理と情報抽出の基本機能を実装。"""

import json
from PIL import Image
from io import BytesIO

class CommonGemini:
    """
    汎用クラス CommonGemini

    画像ファイルのパスまたは画像データ (bytes) を入力として受け取り、
    画像情報（幅、高さ、形式、モードなど）を含む JSON を返却します。
    """
    def __init__(self):
        # 追加の初期化が必要な場合はここに記述
        pass

    @staticmethod
    def process_image(image_path):
        """
        画像ファイルのパスを渡して画像情報を取得する

        Arguments:
            image_path: 処理する画像ファイルのパス

        Returns:
            画像情報を含んだ JSON 文字列
        """
        try:
            with Image.open(image_path) as img:
                data = {
                    "status": "success",
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
        except Exception as e:
            data = {
                "status": "error",
                "message": str(e)
            }
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def process_image_bytes(image_bytes):
        """
        画像データ (bytes) を渡して画像情報を取得する

        Arguments:
            image_bytes: 処理する画像データ (bytes)

        Returns:
            画像情報を含んだ JSON 文字列
        """
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                data = {
                    "status": "success",
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
        except Exception as e:
            data = {
                "status": "error",
                "message": str(e)
            }
        return json.dumps(data, ensure_ascii=False)

if __name__ == '__main__':
    import sys
    # コマンドプロンプトから画像ファイルのパスを受け取り処理を行う
    if len(sys.argv) != 2:
        print("使用法: python common_gemini.py 画像ファイルのパス")
        sys.exit(1)

    image_path = sys.argv[1]
    result_json = CommonGemini.process_image(image_path)
    print(result_json) 