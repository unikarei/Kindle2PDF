"""
Kindle本を自動的にスクリーンショットしてPDFに変換するアプリケーション
警告: このツールは個人的なバックアップ目的のみに使用してください。
     Amazonの利用規約を確認し、DRM保護されたコンテンツの扱いには注意してください。
"""

import os
import time
import json
import hashlib
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyautogui
from PIL import Image
import img2pdf
import re
from pynput import keyboard


class KindleToPDF:
    """Kindle本をPDFに変換するクラス"""
    
    def __init__(self, config_path="config.json"):
        """
        初期化
        
        Args:
            config_path (str): 設定ファイルのパス
        """
        self.config = self.load_config(config_path)
        self.output_dir = self.config.get("output_dir", "kindle_screenshots")
        self.total_pages = self.config.get("total_pages", None)  # Noneの場合は自動検出
        self.page_delay = self.config.get("page_delay", 1.5)
        self.capture_mode = None  # キャプチャモード（manual/auto_detect/auto_complete）
        
        # screenshot_regionの処理
        region = self.config.get("screenshot_region", None)
        self.screenshot_region = tuple(region) if region else None
        
        self.driver = None
        self.images = []
        self.last_page_state = None  # 最終ページ検出用
        self.user_stop_requested = False  # ユーザーによる手動終了フラグ
        self.keyboard_listener = None  # キーボードリスナー
        
        # 出力ディレクトリの作成
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_config(self, config_path):
        """
        設定ファイルを読み込む
        
        Args:
            config_path (str): 設定ファイルのパス
            
        Returns:
            dict: 設定情報
        """
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"警告: 設定ファイル '{config_path}' が見つかりません。デフォルト設定を使用します。")
            return {}
    
    def start_keyboard_listener(self):
        """
        キーボードリスナーを開始（Ctrl+Xで終了）
        """
        def on_press(key):
            try:
                # Ctrl+X の検出
                if hasattr(key, 'char') and key.char == '\x18':  # Ctrl+X
                    print("\n\n" + "="*70)
                    print("⚠️  Ctrl+X が押されました！")
                    print("キャプチャを終了します...")
                    print("="*70 + "\n")
                    self.user_stop_requested = True
                    return False  # リスナーを停止
            except AttributeError:
                pass
        
        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        self.keyboard_listener.start()
        print("\n💡 ヒント: キャプチャ中に Ctrl+X を押すといつでも終了できます\n")
    
    def stop_keyboard_listener(self):
        """
        キーボードリスナーを停止
        """
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def setup_browser(self):
        """
        Chromeブラウザをセットアップする
        """
        print("ブラウザを起動しています...")
        
        # ChromeDriverを自動的にダウンロード・セットアップ
        service = Service(ChromeDriverManager().install())
        
        # ブラウザオプションの設定
        options = webdriver.ChromeOptions()
        
        # クラッシュを防ぐための安定化オプション
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")  # GPUアクセラレーションを無効化
        options.add_argument("--disable-software-rasterizer")
        
        # Selenium検出を回避する設定
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agentを通常のブラウザに設定
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # ログレベルを設定してエラー表示を抑制
        options.add_argument("--log-level=3")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # 既存のChromeプロファイルを使用する場合（オプション）
        use_profile = self.config.get("use_chrome_profile", False)
        if use_profile:
            user_data_dir = self.config.get("chrome_user_data_dir", "")
            if user_data_dir:
                options.add_argument(f"user-data-dir={user_data_dir}")
                print(f"Chromeプロファイルを使用: {user_data_dir}")
        
        # 全画面表示にする場合
        if self.config.get("fullscreen", False):
            options.add_argument("--start-maximized")
        
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Selenium検出を回避するJavaScriptを実行
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            print("✓ ブラウザの起動に成功しました")
            
        except Exception as e:
            print(f"✗ ブラウザの起動に失敗しました: {e}")
            raise
        
    def open_kindle_cloud_reader(self):
        """
        Kindle Cloud Readerを開く
        """
        # URLを開くかスキップするか
        skip_url = self.config.get("skip_url_open", False)
        
        if not skip_url:
            print("Kindle Cloud Readerを開いています...")
            
            # 日本のAmazonを使用（設定で変更可能）
            kindle_url = self.config.get("kindle_url", "https://read.amazon.co.jp/kindle-library")
            self.driver.get(kindle_url)
            
            # ページが完全に読み込まれるまで少し待つ
            time.sleep(3)
            
            # ログイン時間を待つ
            print("\n" + "="*60)
            print("【重要】手動でログインし、読みたい本を開いてください。")
            print("")
            print("1. Amazonにログイン")
            print("2. 本を選択して開く（新しいタブで開きます）")
            print("3. 本の最初のページ（1ページ目）に移動")
            print("4. F11キーで全画面モードにする（推奨）")
            print("5. ページめくり方向を確認")
            print("   - 左矢印キーで次のページに進む場合: config.jsonで \"page_turn_direction\": \"left\"")
            print("   - 右矢印キーで次のページに進む場合: config.jsonで \"page_turn_direction\": \"right\"")
            print("6. ブラウザウィンドウをアクティブな状態にする")
            print("")
            print("準備ができたら、このターミナルに戻ってEnterキーを押してください。")
            print("="*60 + "\n")
            input()
            
            # 新しく開いたタブに切り替え
            print("本が開かれたタブを検出しています...")
            time.sleep(2)
            
            # すべてのウィンドウハンドルを取得
            all_windows = self.driver.window_handles
            print(f"開いているタブ数: {len(all_windows)}")
            
            if len(all_windows) > 1:
                # 最後に開かれたタブ（本のタブ）に切り替え
                self.driver.switch_to.window(all_windows[-1])
                print(f"✓ 本のタブに切り替えました")
                print(f"  現在のURL: {self.driver.current_url}")
                
                # ブラウザウィンドウをアクティブにする（F11全画面を維持）
                try:
                    # maximize_window()は呼ばない（F11全画面モードを解除してしまうため）
                    # 代わりにJavaScriptでフォーカスのみ設定
                    self.driver.execute_script("window.focus();")
                    time.sleep(0.5)
                    print(f"✓ ブラウザウィンドウにフォーカスしました（全画面モード維持）")
                except Exception as e:
                    print(f"  警告: ウィンドウのフォーカスに失敗: {e}")
                
            else:
                print("警告: 新しいタブが検出されませんでした。")
                print("本は同じタブで開いている可能性があります。")
                
                # 現在のタブをアクティブにする（F11全画面を維持）
                try:
                    self.driver.execute_script("window.focus();")
                    time.sleep(0.5)
                    print(f"✓ ブラウザウィンドウにフォーカスしました（全画面モード維持）")
                except Exception as e:
                    print(f"  警告: ウィンドウのフォーカスに失敗: {e}")
                
        else:
            print("既存のブラウザタブを使用します。")
            print("\n" + "="*60)
            print("【重要】事前に以下を完了させてください：")
            print("")
            print("1. Chromeで Kindle Cloud Reader を開く")
            print("2. 読みたい本を開く")
            print("3. 本の最初のページ（1ページ目）に移動")
            print("4. F11キーで全画面モードにする（推奨）")
            print("5. そのままにしておく（閉じないでください）")
            print("")
            print("準備ができたら、このターミナルに戻ってEnterキーを押してください。")
            print("="*60 + "\n")
            input()
            
            print("既存のブラウザウィンドウに接続しています...")
            time.sleep(1)
        
        # ブラウザをアクティブにする
        time.sleep(1)
    
    def select_capture_mode(self):
        """
        キャプチャモードを選択する
        
        Returns:
            str: 選択されたモード（'manual', 'auto_detect', 'auto_complete'）
        """
        print("\n" + "="*70)
        print("キャプチャモードを選択してください")
        print("="*70)
        print()
        print("1. 手動入力モード")
        print("   - 総ページ数を手動で入力します")
        print("   - 最も確実で高速な方法")
        print()
        print("2. 自動検出モード（ページ番号表示から）")
        print("   - 画面に表示されているページ番号（例: 5/196）から検出")
        print("   - ページ番号が表示されている場合に有効")
        print()
        print("3. 自動完了モード（最終ページまで自動）")
        print("   - 最終ページに到達するまで自動的にキャプチャ")
        print("   - ページ数不明でも完全自動化")
        print("   - やや時間がかかる可能性あり")
        print()
        print("="*70)
        
        while True:
            choice = input("モードを選択してください (1/2/3): ").strip()
            if choice == '1':
                return 'manual'
            elif choice == '2':
                return 'auto_detect'
            elif choice == '3':
                return 'auto_complete'
            else:
                print("無効な選択です。1, 2, または 3 を入力してください。")
        
    def detect_total_pages(self):
        """
        Kindle Cloud Readerから総ページ数を自動検出する
        
        Returns:
            int: 検出されたページ数、検出失敗時はNone
        """
        print("\n総ページ数を自動検出中...")
        
        try:
            # 複数のパターンでページ情報を探す
            selectors = [
                # Kindle Cloud Readerのページ表示（例: "5 / 196"）
                "div[class*='page']",
                "span[class*='page']",
                "div[class*='position']",
                "div[class*='location']",
                # より広範囲な検索
                "div", "span"
            ]
            
            # 正規表現パターン（例: "5 / 196", "5/196", "Page 5 of 196"）
            patterns = [
                r'(\d+)\s*/\s*(\d+)',  # "5 / 196" または "5/196"
                r'Page\s+(\d+)\s+of\s+(\d+)',  # "Page 5 of 196"
                r'(\d+)\s+/\s+(\d+)\s+ページ',  # "5 / 196 ページ"
                r'位置\s+\d+\s*/\s*(\d+)',  # "位置 500 / 3000"（位置から推定）
            ]
            
            # ページ全体のテキストを取得して検索
            page_source = self.driver.page_source
            print(f"  ページソースを取得しました（{len(page_source)}文字）")
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    print(f"  パターンマッチ: {pattern}")
                    print(f"  マッチ結果: {matches}")
                    
                    # 最大のページ数を取得
                    if len(matches[0]) == 2:
                        # 2つの数字がある場合（現在ページ / 総ページ）
                        total = max([int(m[1]) for m in matches])
                    else:
                        # 1つの数字の場合（総ページのみ）
                        total = max([int(m[0] if isinstance(m, tuple) else m) for m in matches])
                    
                    print(f"  ✓ 総ページ数を検出: {total}ページ")
                    return total
            
            # JavaScriptで要素を検索
            print("  JavaScriptで要素を検索中...")
            js_code = """
            function findPageInfo() {
                // すべてのテキストノードを検索
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                const patterns = [
                    /(\d+)\s*\/\s*(\d+)/,
                    /Page\s+(\d+)\s+of\s+(\d+)/i,
                    /(\d+)\s+\/\s+(\d+)\s+ページ/
                ];
                
                let results = [];
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    for (let pattern of patterns) {
                        const match = text.match(pattern);
                        if (match) {
                            results.push({
                                text: text,
                                current: parseInt(match[1]),
                                total: parseInt(match[2])
                            });
                        }
                    }
                }
                
                return results;
            }
            
            return findPageInfo();
            """
            
            page_info = self.driver.execute_script(js_code)
            
            if page_info and len(page_info) > 0:
                print(f"  JavaScriptで検出: {page_info}")
                # 最大の総ページ数を取得
                total = max([info['total'] for info in page_info])
                print(f"  ✓ 総ページ数を検出: {total}ページ")
                return total
            
            print("  ✗ ページ数を検出できませんでした")
            return None
            
        except Exception as e:
            print(f"  ✗ ページ数の検出中にエラー: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_page_state(self):
        """
        現在のページ状態を取得
        
        Returns:
            dict: ページの状態情報
        """
        state = {
            'url': self.driver.current_url,
            'page_source_hash': hashlib.md5(self.driver.page_source.encode()).hexdigest(),
            'page_content_hash': None,
            'page_info': None,
            'body_text_hash': None
        }
        
        try:
            # ページコンテンツのハッシュを取得（より正確）
            js_result = self.driver.execute_script("""
                // ページ表示領域のテキスト内容を取得
                var contentElement = document.querySelector('[id*="reader"], [class*="reader"], [class*="content"]');
                if (contentElement) {
                    return {
                        content: contentElement.innerText,
                        html: contentElement.innerHTML.substring(0, 1000)
                    };
                }
                
                // フォールバック: body全体
                return {
                    content: document.body.innerText,
                    html: document.body.innerHTML.substring(0, 1000)
                };
            """)
            
            if js_result:
                state['page_content_hash'] = hashlib.md5(js_result['content'].encode()).hexdigest()
                state['body_text_hash'] = hashlib.md5(js_result['content'][:500].encode()).hexdigest()
            
            # ページ番号情報を取得
            page_info = self.driver.execute_script("""
                function findPageInfo() {
                    var walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    var pattern = /(\\d+)\\s*\\/\\s*(\\d+)/;
                    var node;
                    while (node = walker.nextNode()) {
                        var text = node.textContent.trim();
                        var match = text.match(pattern);
                        if (match) {
                            return {
                                text: text,
                                current: parseInt(match[1]),
                                total: parseInt(match[2])
                            };
                        }
                    }
                    return null;
                }
                return findPageInfo();
            """)
            
            state['page_info'] = page_info
            
        except Exception as e:
            pass  # エラーは無視
        
        return state
    
    def is_last_page(self, before_state, after_state):
        """
        最終ページかどうかを判定
        
        Args:
            before_state: ページ送り前の状態
            after_state: ページ送り後の状態
        
        Returns:
            tuple: (is_last, reasons, confidence)
        """
        reasons = []
        confidence = 0
        
        # 1. URL比較
        if before_state['url'] == after_state['url']:
            reasons.append("URL変化なし")
            confidence += 30
        
        # 2. ページコンテンツのハッシュ比較（最重要）
        if before_state['page_content_hash'] and after_state['page_content_hash']:
            if before_state['page_content_hash'] == after_state['page_content_hash']:
                reasons.append("コンテンツ変化なし")
                confidence += 40
        
        # 3. body全体のハッシュ比較
        if before_state['page_source_hash'] == after_state['page_source_hash']:
            reasons.append("ソース変化なし")
            confidence += 10
        
        # 4. ページ番号情報の比較
        if before_state['page_info'] and after_state['page_info']:
            before_page = before_state['page_info']['current']
            after_page = after_state['page_info']['current']
            total_pages = before_state['page_info']['total']
            
            if before_page == after_page:
                reasons.append(f"ページ番号変化なし ({before_page}/{total_pages})")
                confidence += 20
            
            if before_page == total_pages or after_page == total_pages:
                reasons.append(f"最終ページ番号到達 ({total_pages}/{total_pages})")
                confidence += 30
        
        # 判定: confidence が 50 以上なら最終ページ
        is_last = confidence >= 50
        
        return is_last, reasons, confidence
        
    def take_screenshot(self, page_num):
        """
        ページのスクリーンショットを撮る
        
        Args:
            page_num (int): ページ番号
            
        Returns:
            str: スクリーンショットのファイルパス
        """
        screenshot_path = os.path.join(self.output_dir, f"page_{page_num:04d}.png")
        
        if self.screenshot_region:
            # 指定された領域のみスクリーンショット
            pyautogui.screenshot(screenshot_path, region=self.screenshot_region)
        else:
            # 画面全体のスクリーンショット
            pyautogui.screenshot(screenshot_path)
        
        return screenshot_path
    
    def next_page(self):
        """
        次のページに移動する
        """
        print(f"\n  --- ページ送り開始 ---")
        
        # ページめくり方向を設定から取得
        page_turn_direction = self.config.get("page_turn_direction", "left").lower()
        if page_turn_direction == "left":
            arrow_key = Keys.ARROW_LEFT
            arrow_name = "ArrowLeft"
            arrow_code = 37
            pyautogui_key = "left"
            direction_text = "左"
        elif page_turn_direction == "right":
            arrow_key = Keys.ARROW_RIGHT
            arrow_name = "ArrowRight"
            arrow_code = 39
            pyautogui_key = "right"
            direction_text = "右"
        else:
            print(f"  ✗ エラー: 不正な page_turn_direction 設定: {page_turn_direction}")
            print(f"     'left' または 'right' を指定してください")
            return False
        
        print(f"  ページめくり方向: {direction_text}矢印キー")
        
        # ブラウザが有効か確認
        try:
            # 現在のURLを確認
            current_url = self.driver.current_url
            print(f"  現在のURL: {current_url[:80]}...")
            
            # ブラウザウィンドウを強制的にアクティブにする
            self.driver.switch_to.window(self.driver.current_window_handle)
            print(f"  ✓ ウィンドウハンドルに切り替え完了")
            
            # Seleniumでブラウザを前面に持ってくる
            self.driver.execute_script("window.focus();")
            print(f"  ✓ window.focus() 実行完了")
            
            # 少し待ってフォーカスが移るのを確実にする
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ エラー: ブラウザのフォーカス切り替えに失敗: {e}")
            return False
        
        # 方法1: Seleniumでキーを送る
        print(f"  試行1: Selenium Keys.{arrow_name.upper()} (次のページへ)")
        try:
            body = self.driver.find_element("tag name", "body")
            print(f"    ✓ body要素を取得")
            body.send_keys(arrow_key)
            print(f"    ✓ Keys.{arrow_name.upper()} を送信")
            time.sleep(1)  # ページ遷移を待つ
            
            # URLが変わったか確認
            new_url = self.driver.current_url
            if new_url != current_url:
                print(f"    ✓ ページ遷移検出: URL変更あり")
            else:
                print(f"    ? URL変更なし（同一ページの可能性）")
            
            print(f"  ✓ 方法1成功: Selenium Keys.{arrow_name.upper()}")
            success = True
            
        except Exception as e:
            print(f"  ✗ 方法1失敗: {e}")
            
            # 方法2: JavaScript経由でイベントを発火
            print(f"  試行2: JavaScript KeyboardEvent ({arrow_name})")
            try:
                self.driver.execute_script(f"""
                    console.log('JavaScript: キーイベント送信開始');
                    var event = new KeyboardEvent('keydown', {{
                        key: '{arrow_name}',
                        code: '{arrow_name}',
                        keyCode: {arrow_code},
                        which: {arrow_code},
                        bubbles: true,
                        cancelable: true
                    }});
                    document.dispatchEvent(event);
                    console.log('JavaScript: キーイベント送信完了');
                    
                    // ページ番号要素があれば取得
                    var pageInfo = document.querySelector('[class*="page"]');
                    if (pageInfo) {{
                        console.log('現在のページ情報:', pageInfo.textContent);
                    }}
                """)
                print(f"    ✓ JavaScript実行完了")
                time.sleep(1)
                
                new_url = self.driver.current_url
                if new_url != current_url:
                    print(f"    ✓ ページ遷移検出: URL変更あり")
                else:
                    print(f"    ? URL変更なし")
                
                print(f"  ✓ 方法2成功: JavaScript KeyboardEvent")
                success = True
                
            except Exception as e2:
                print(f"  ✗ 方法2失敗: {e2}")
                
                # 方法3: クリック + PyAutoGUI
                print(f"  試行3: PyAutoGUI（画面中央クリック + {direction_text}矢印）")
                try:
                    # maximize_window()は呼ばない（F11全画面モードを解除してしまうため）
                    
                    import pyautogui
                    # 画面中央をクリック
                    screen_width, screen_height = pyautogui.size()
                    click_x = screen_width // 2
                    click_y = screen_height // 2
                    print(f"    クリック位置: ({click_x}, {click_y})")
                    pyautogui.click(click_x, click_y)
                    time.sleep(0.3)
                    print(f"    ✓ クリック完了")
                    
                    # 矢印キーを送信
                    pyautogui.press(pyautogui_key)
                    print(f"    ✓ {direction_text}矢印キー送信完了")
                    time.sleep(1)
                    
                    print(f"  ✓ 方法3成功: PyAutoGUI")
                    success = True
                    
                except Exception as e3:
                    print(f"  ✗ 方法3失敗: {e3}")
                    print(f"  ✗✗✗ すべてのページ送り方法が失敗しました ✗✗✗")
                    success = False
        
        # ページ遷移を待つ
        print(f"  待機中: {self.page_delay}秒")
        time.sleep(self.page_delay)
        
        print(f"  --- ページ送り終了 (成功: {success}) ---\n")
        return success
    
    def capture_all_pages(self):
        """
        すべてのページをキャプチャする
        """
        # キャプチャモードを選択
        if self.capture_mode is None:
            self.capture_mode = self.select_capture_mode()
        
        print(f"\n選択されたモード: {self.capture_mode}\n")
        
        # モード別の処理
        if self.capture_mode == 'manual':
            # 手動入力モード
            if self.total_pages is None:
                user_input = input("総ページ数を入力してください: ").strip()
                self.total_pages = int(user_input) if user_input else 100
            print(f"\n設定されたページ数: {self.total_pages}ページ\n")
            self._capture_with_page_count()
            
        elif self.capture_mode == 'auto_detect':
            # 自動検出モード（ページ番号から）
            detected_pages = self.detect_total_pages()
            if detected_pages:
                self.total_pages = detected_pages
                print(f"\n✓ 自動検出された総ページ数: {self.total_pages}ページ\n")
                self._capture_with_page_count()
            else:
                print("\n総ページ数が検出できませんでした。")
                user_input = input("手動でページ数を入力してください: ").strip()
                if user_input:
                    self.total_pages = int(user_input)
                    self._capture_with_page_count()
                else:
                    print("自動完了モードに切り替えます...\n")
                    self.capture_mode = 'auto_complete'
                    self._capture_until_last_page()
        
        elif self.capture_mode == 'auto_complete':
            # 自動完了モード（最終ページまで）
            self._capture_until_last_page()
    
    def _capture_with_page_count(self):
        """
        ページ数指定でキャプチャする
        """
        print(f"\n{self.total_pages}ページのスクリーンショットを開始します...\n")
        
        # キーボードリスナーを開始
        self.start_keyboard_listener()
        
        # 開始前にブラウザを確実にアクティブ化（F11全画面モードを維持）
        try:
            self.driver.switch_to.window(self.driver.current_window_handle)
            # maximize_window()は呼ばない（F11全画面モードを解除してしまうため）
            self.driver.execute_script("window.focus();")
            time.sleep(1)
            print("✓ キャプチャ開始前にブラウザにフォーカスしました（全画面モード維持）\n")
        except Exception as e:
            print(f"警告: ブラウザのフォーカスに失敗: {e}\n")
        
        for page in range(1, self.total_pages + 1):
            # ユーザーによる手動終了チェック
            if self.user_stop_requested:
                print(f"\n✓ ユーザーによって手動終了されました（{page-1}ページまでキャプチャ完了）")
                break
            print(f"ページ {page}/{self.total_pages} をキャプチャ中...")
            
            # ブラウザが有効か確認
            try:
                current_url = self.driver.current_url
                print(f"  現在のURL: {current_url[:80]}...")
            except Exception as e:
                print(f"\nエラー: ブラウザが閉じられたか、応答していません: {e}")
                print("処理を中断します。")
                break
            
            # スクリーンショットを撮る
            try:
                screenshot_path = self.take_screenshot(page)
                self.images.append(screenshot_path)
                print(f"  ✓ スクリーンショット保存: {screenshot_path}")
            except Exception as e:
                print(f"  ✗ スクリーンショット失敗: {e}")
                continue
            
            # 最後のページでなければ次のページへ
            if page < self.total_pages:
                success = self.next_page()
                if not success:
                    print(f"\n警告: ページ送りに失敗しました。処理を続行しますか？")
                    self.stop_keyboard_listener()  # 入力待ち前にリスナー停止
                    response = input("続行する場合はEnterキーを押してください（中断する場合はCtrl+C）: ")
                    if not self.user_stop_requested:  # まだ終了要求がなければ再開
                        self.start_keyboard_listener()
        
        # キーボードリスナーを停止
        self.stop_keyboard_listener()
        
        print(f"\n✓ {len(self.images)}ページのキャプチャが完了しました！")
    
    def _capture_until_last_page(self):
        """
        最終ページまで自動的にキャプチャする
        """
        print("\n最終ページに到達するまで自動的にキャプチャします...\n")
        
        # キーボードリスナーを開始
        self.start_keyboard_listener()
        
        # 開始前にブラウザを確実にアクティブ化
        try:
            self.driver.switch_to.window(self.driver.current_window_handle)
            self.driver.execute_script("window.focus();")
            time.sleep(1)
            print("✓ キャプチャ開始前にブラウザにフォーカスしました\n")
        except Exception as e:
            print(f"警告: ブラウザのフォーカスに失敗: {e}\n")
        
        page = 1
        max_pages = 1000  # 安全のための上限
        
        while page <= max_pages:
            # ユーザーによる手動終了チェック
            if self.user_stop_requested:
                print(f"\n✓ ユーザーによって手動終了されました（{page-1}ページまでキャプチャ完了）")
                break
            print(f"ページ {page} をキャプチャ中...")
            
            # ブラウザが有効か確認
            try:
                current_url = self.driver.current_url
                print(f"  現在のURL: {current_url[:80]}...")
            except Exception as e:
                print(f"\nエラー: ブラウザが閉じられたか、応答していません: {e}")
                print("処理を中断します。")
                break
            
            # ページ送り前の状態を取得
            before_state = self.get_page_state()
            if before_state['page_info']:
                print(f"  ページ番号表示: {before_state['page_info']['current']} / {before_state['page_info']['total']}")
            
            # スクリーンショットを撮る
            try:
                screenshot_path = self.take_screenshot(page)
                self.images.append(screenshot_path)
                print(f"  ✓ スクリーンショット保存: {screenshot_path}")
            except Exception as e:
                print(f"  ✗ スクリーンショット失敗: {e}")
                break
            
            # 次のページへ移動を試みる
            print(f"\n  次のページへ移動中...")
            success = self.next_page()
            
            if not success:
                print(f"\n⚠️  ページ送りに失敗しました。")
                self.stop_keyboard_listener()  # 入力待ち前にリスナー停止
                response = input("最終ページに到達した可能性があります。終了しますか？ (y/n): ").strip().lower()
                if response == 'y':
                    print("キャプチャを終了します。")
                    break
                else:
                    print("続行します...")
                    if not self.user_stop_requested:  # まだ終了要求がなければ再開
                        self.start_keyboard_listener()
                    page += 1
                    continue
            
            # ページ送り後の状態を取得
            after_state = self.get_page_state()
            
            # 最終ページ判定
            is_last, reasons, confidence = self.is_last_page(before_state, after_state)
            
            if is_last:
                print(f"\n{'='*70}")
                print(f"✓ 最終ページを検出しました！")
                print(f"  信頼度: {confidence}%")
                print(f"  検出理由:")
                for reason in reasons:
                    print(f"    - {reason}")
                print(f"{'='*70}")
                print(f"\nキャプチャを終了します。")
                break
            
            # 次のページへ
            page += 1
            
            # 進捗表示
            if page % 10 == 0:
                print(f"\n--- {page}ページまでキャプチャ完了 ---\n")
        
        else:
            print(f"\n⚠️  警告: {max_pages}ページに到達しました。安全のため処理を終了します。")
        
        # キーボードリスナーを停止
        self.stop_keyboard_listener()
        
        print(f"\n✓ {len(self.images)}ページのキャプチャが完了しました！")
    
    def create_pdf(self, output_filename=None):
        """
        画像をPDFに変換する
        
        Args:
            output_filename (str): 出力PDFファイル名
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"kindle_book_{timestamp}.pdf"
        
        print(f"\nPDFを作成しています: {output_filename}")
        
        try:
            with open(output_filename, "wb") as f:
                f.write(img2pdf.convert(self.images))
            print(f"✓ PDF作成完了: {output_filename}")
        except Exception as e:
            print(f"✗ PDFの作成中にエラーが発生しました: {e}")
    
    def cleanup(self):
        """
        クリーンアップ処理
        """
        # キーボードリスナーを停止
        self.stop_keyboard_listener()
        
        if self.driver:
            self.driver.quit()
        
        # スクリーンショット画像の削除（オプション）
        if self.config.get("delete_screenshots", False):
            print("\nスクリーンショット画像を削除しています...")
            for img_path in self.images:
                try:
                    os.remove(img_path)
                except Exception as e:
                    print(f"警告: {img_path} の削除に失敗しました: {e}")
    
    def run(self):
        """
        メイン処理を実行する
        """
        try:
            # ブラウザのセットアップ
            self.setup_browser()
            
            # Kindle Cloud Readerを開く
            self.open_kindle_cloud_reader()
            
            # すべてのページをキャプチャ
            self.capture_all_pages()
            
            # PDFを作成
            pdf_filename = self.config.get("pdf_filename", None)
            self.create_pdf(pdf_filename)
            
            print("\n処理が正常に完了しました！")
            
        except KeyboardInterrupt:
            print("\n\n処理が中断されました。")
        except Exception as e:
            print(f"\n\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # クリーンアップ
            self.cleanup()


def main():
    """
    メイン関数
    """
    print("="*60)
    print("Kindle to PDF Converter")
    print("="*60)
    print("\n【注意事項】")
    print("- このツールは個人的なバックアップ目的のみに使用してください")
    print("- Amazonの利用規約を確認してください")
    print("- DRM保護されたコンテンツの扱いには十分注意してください")
    print("="*60 + "\n")
    
    # アプリケーションの実行
    app = KindleToPDF()
    app.run()


if __name__ == "__main__":
    main()
