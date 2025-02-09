#!/usr/bin/env python
import os
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

# 既存の gemini.py のアップロード関数に類似した関数を利用しています。
def upload_to_gemini(path, mime_type=None):
    """
    Geminiにファイルをアップロードする関数
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def main():
    # 環境変数から API キーを設定
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    # Gemini 用の生成設定 (sample/gemini.py から拝借)
    generation_config = {
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
                ),
                "tax rate": content.Schema(
                    type=content.Type.INTEGER,
                ),
                "Representative Item Name": content.Schema(
                    type=content.Type.STRING,
                ),
            },
        ),
        "response_mime_type": "application/json",
    }

    # Geminiモデルの作成（システム命令を領収書抽出向けに変更）
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction=(
            "次の画像から領収書の情報を抽出してください。必要な情報は:\n"
            "- 取引日 (yyyy/mm/dd、時間無し)\n"
            "- 店舗名\n"
            "- 合計金額 (通貨記号を除く)\n"
            "- 税額対象金額\n"
            "- 税率\n"
            "- 税額\n"
            "- 代表的な商品名（最も高額な商品や特徴的な商品を1つ）\n"
            "出力は JSON 形式でお願いします。"
        ),
    )

    # 画像ファイルのアップロード（ファイル名を IMG_2851.jpg に変更）
    receipt_file = upload_to_gemini("IMG_2851.jpg", mime_type="image/jpeg")

    # チャットセッション開始（初期メッセージとして画像ファイルを送信）
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    receipt_file,
                ],
            },
        ]
    )

    # モデルに領収書の情報抽出を指示するメッセージを送信
    response = chat_session.send_message("領収書の詳細情報を抽出してください。")
    print(response.text)

if __name__ == '__main__':
    main() 