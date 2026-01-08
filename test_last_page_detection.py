"""
最終ページ検出手法の検証スクリプト
Kindle本で「これ以上めくれない」状態を検出する複数の方法をテストします
"""

import json
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pyautogui


def setup_browser():
    """ブラウザをセットアップ"""
    print("ブラウザを起動しています...")
    
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    
    return driver


def get_page_state(driver):
    """
    現在のページ状態を取得
    
    Returns:
        dict: ページの状態情報
    """
    state = {
        'url': driver.current_url,
        'page_source_hash': hashlib.md5(driver.page_source.encode()).hexdigest(),
        'page_content_hash': None,
        'page_info': None,
        'body_text_hash': None
    }
    
    try:
        # ページコンテンツのハッシュを取得（より正確）
        js_result = driver.execute_script("""
            // ページ表示領域のテキスト内容を取得
            var contentElement = document.querySelector('[id*="reader"], [class*="reader"], [class*="content"]');
            if (contentElement) {
                return {
                    content: contentElement.innerText,
                    html: contentElement.innerHTML.substring(0, 1000)  // 最初の1000文字
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
        page_info = driver.execute_script("""
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
        print(f"  警告: ページ状態取得エラー: {e}")
    
    return state


def is_last_page(before_state, after_state):
    """
    最終ページかどうかを判定
    
    Args:
        before_state: ページ送り前の状態
        after_state: ページ送り後の状態
    
    Returns:
        tuple: (is_last, reason, confidence)
    """
    reasons = []
    confidence = 0
    
    # 1. URL比較（最も確実）
    if before_state['url'] == after_state['url']:
        reasons.append("URL変化なし")
        confidence += 30
    
    # 2. ページコンテンツのハッシュ比較
    if before_state['page_content_hash'] and after_state['page_content_hash']:
        if before_state['page_content_hash'] == after_state['page_content_hash']:
            reasons.append("コンテンツ変化なし")
            confidence += 40
    
    # 3. body全体のハッシュ比較（参考程度）
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
    
    # 判定: confidence が 50 以上なら最終ページと判定
    is_last = confidence >= 50
    
    return is_last, reasons, confidence


def send_page_turn(driver, direction="left"):
    """ページをめくる"""
    arrow_key = Keys.ARROW_LEFT if direction == "left" else Keys.ARROW_RIGHT
    
    try:
        body = driver.find_element("tag name", "body")
        body.send_keys(arrow_key)
        return True
    except Exception as e:
        print(f"  ページ送りエラー: {e}")
        return False


def main():
    """メイン処理"""
    print("="*70)
    print("最終ページ検出手法の検証")
    print("="*70)
    print()
    
    # 設定を読み込む
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        config = {}
    
    driver = None
    
    try:
        # ブラウザセットアップ
        driver = setup_browser()
        
        # Kindle Cloud Readerを開く
        kindle_url = config.get("kindle_url", "https://read.amazon.co.jp/kindle-library")
        print(f"{kindle_url} を開いています...")
        driver.get(kindle_url)
        time.sleep(3)
        
        # ログインと本を開く
        print("\n" + "="*70)
        print("【操作が必要です】")
        print("1. Amazonにログイン")
        print("2. 本を選択して開く")
        print("3. 本の最後から2～3ページ前に移動してください")
        print("   （最終ページ検出をテストするため）")
        print("")
        print("準備ができたら、Enterキーを押してください。")
        print("="*70 + "\n")
        input()
        
        # 新しいタブに切り替え
        all_windows = driver.window_handles
        if len(all_windows) > 1:
            driver.switch_to.window(all_windows[-1])
            print(f"✓ 本のタブに切り替えました\n")
        
        time.sleep(2)
        
        # ページめくり方向
        direction = config.get("page_turn_direction", "left")
        print(f"ページめくり方向: {direction}矢印キー\n")
        
        # テストループ
        print("="*70)
        print("ページ送りテスト開始（最大10回まで）")
        print("="*70)
        
        for i in range(1, 11):
            print(f"\n--- テスト {i}/10 ---")
            
            # ページ送り前の状態を取得
            print("  ページ送り前の状態を取得中...")
            before_state = get_page_state(driver)
            
            if before_state['page_info']:
                print(f"    ページ番号: {before_state['page_info']['current']} / {before_state['page_info']['total']}")
            print(f"    URL: {before_state['url'][:60]}...")
            print(f"    コンテンツハッシュ: {before_state['page_content_hash'][:16]}...")
            
            # ページを送る
            print(f"  {direction}矢印キーでページ送り...")
            if not send_page_turn(driver, direction):
                print("  ✗ ページ送り失敗")
                break
            
            time.sleep(2)  # ページ遷移を待つ
            
            # ページ送り後の状態を取得
            print("  ページ送り後の状態を取得中...")
            after_state = get_page_state(driver)
            
            if after_state['page_info']:
                print(f"    ページ番号: {after_state['page_info']['current']} / {after_state['page_info']['total']}")
            print(f"    URL: {after_state['url'][:60]}...")
            print(f"    コンテンツハッシュ: {after_state['page_content_hash'][:16]}...")
            
            # 最終ページ判定
            is_last, reasons, confidence = is_last_page(before_state, after_state)
            
            print(f"\n  判定結果:")
            print(f"    最終ページ: {'YES' if is_last else 'NO'}")
            print(f"    信頼度: {confidence}%")
            if reasons:
                print(f"    理由:")
                for reason in reasons:
                    print(f"      - {reason}")
            
            if is_last:
                print(f"\n{'='*70}")
                print(f"✓ 最終ページを検出しました！")
                print(f"  信頼度: {confidence}%")
                print(f"  検出理由: {', '.join(reasons)}")
                print(f"{'='*70}")
                break
            
            # 次のテストへ
            print(f"  → 次のページへ進みます...")
        
        else:
            print(f"\n{'='*70}")
            print("10回のテストが完了しましたが、最終ページは検出されませんでした")
            print(f"{'='*70}")
        
        print("\nブラウザは10秒後に自動的に閉じます...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n\n処理が中断されました。")
    except Exception as e:
        print(f"\n\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("\nブラウザを閉じました。")


if __name__ == "__main__":
    main()
