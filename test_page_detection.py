"""
総ページ数の自動検出機能をテストするスクリプト
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re


def setup_browser():
    """ブラウザをセットアップ"""
    print("ブラウザを起動しています...")
    
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # 基本設定
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    
    # Selenium検出を回避
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Selenium検出を回避するJavaScript
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver


def detect_total_pages(driver):
    """総ページ数を検出"""
    print("\n総ページ数を自動検出中...")
    
    try:
        # ページソースから検索
        page_source = driver.page_source
        print(f"  ページソースを取得（{len(page_source)}文字）")
        
        # 正規表現パターン
        patterns = [
            r'(\d+)\s*/\s*(\d+)',  # "5 / 196"
            r'Page\s+(\d+)\s+of\s+(\d+)',  # "Page 5 of 196"
            r'(\d+)\s+/\s+(\d+)\s+ページ',  # "5 / 196 ページ"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                print(f"  パターンマッチ: {pattern}")
                print(f"  マッチ結果（最初の5件）: {matches[:5]}")
                
                # 最大のページ数を取得
                total = max([int(m[1]) for m in matches])
                print(f"  ✓ 総ページ数を検出: {total}ページ")
                return total
        
        # JavaScriptで検索
        print("  JavaScriptで要素を検索中...")
        js_code = """
        function findPageInfo() {
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
        
        page_info = driver.execute_script(js_code)
        
        if page_info and len(page_info) > 0:
            print(f"  JavaScriptで検出（最初の3件）:")
            for info in page_info[:3]:
                print(f"    - {info}")
            
            total = max([info['total'] for info in page_info])
            print(f"  ✓ 総ページ数を検出: {total}ページ")
            return total
        
        print("  ✗ ページ数を検出できませんでした")
        return None
        
    except Exception as e:
        print(f"  ✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """メイン処理"""
    print("="*60)
    print("総ページ数自動検出テスト")
    print("="*60)
    
    # 設定を読み込む
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"警告: config.jsonの読み込みに失敗: {e}")
        config = {}
    
    driver = None
    
    try:
        # ブラウザセットアップ
        driver = setup_browser()
        
        # Kindle Cloud Readerを開く
        kindle_url = config.get("kindle_url", "https://read.amazon.co.jp/kindle-library")
        print(f"\n{kindle_url} を開いています...")
        driver.get(kindle_url)
        time.sleep(3)
        
        # ログインと本を開く
        print("\n" + "="*60)
        print("【操作が必要です】")
        print("1. Amazonにログイン")
        print("2. 本を選択して開く")
        print("3. 本の任意のページまで進む")
        print("")
        print("準備ができたら、Enterキーを押してください。")
        print("="*60 + "\n")
        input()
        
        # 新しいタブに切り替え
        all_windows = driver.window_handles
        if len(all_windows) > 1:
            driver.switch_to.window(all_windows[-1])
            print(f"✓ 本のタブに切り替えました")
        
        time.sleep(2)
        
        # ページ数を検出
        total_pages = detect_total_pages(driver)
        
        if total_pages:
            print(f"\n{'='*60}")
            print(f"✓ 検出成功: この本は {total_pages} ページです")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("✗ ページ数を検出できませんでした")
            print("ページネーション情報が表示されていない可能性があります")
            print(f"{'='*60}")
        
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
