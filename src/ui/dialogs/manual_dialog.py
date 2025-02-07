from PySide6.QtWidgets import QTextBrowser, QVBoxLayout
from src.ui.dialogs.base_dialog import BaseDialog

class ManualDialog(BaseDialog):
    """マニュアルダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "マニュアル")
        
        # UIの構築
        self._setup_ui()
    
    def _setup_ui(self):
        """UIの構築"""
        # テキストブラウザの作成
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        
        # マニュアルテキストの設定
        manual_text = """


        <h2>Gemini APIキーの取得方法</h2>
        <p>このアプリケーションを使用するには、Google AI StudioのGemini APIキーが必要です。</p>
        
        <h3>APIキーの取得手順：</h3>
        <ol>
            <li>Google AI Studioの<a href="https://aistudio.google.com/prompts/new_chat">ウェブサイト</a>にアクセスします。</li>
            <li>Googleアカウントでログインします。</li>
            <li>「Get API key」をクリックしてAPIキーを取得します。</li>
        </ol>
        
        <h3>APIキーの設定方法：</h3>
        <ol>
            <li>アプリケーションのメニューから「ツール」→「APIキー設定」を選択します。</li>
            <li>「手動で入力」を選択し、コピーしたAPIキーを入力します。</li>
            <li>または、環境変数「GOOGLE_API_KEY」にAPIキーを設定することもできます。</li>
        </ol>
        
        <p><strong>注意：</strong>APIキーは機密情報です。安全に管理してください。</p>

        <h2>読み取り方</h2>
        <p>1. ファイル → フォルダを開く</p>
        <p>2. 画像を選択</p>
        <p>3. 読み取り処理実行</p>
        <p>結果を確認したあとは、チェック→リネーム(ファイル名)できる</p>
        <p>ダブルクリックで編集できる。csv出力できる</p>
        
                
        """
        self.text_browser.setHtml(manual_text)
        
        # レイアウトの組み立て
        self.layout.addWidget(self.text_browser)
        self.layout.addWidget(self.button_box)
        
        # サイズの調整
        self.resize(600, 400) 