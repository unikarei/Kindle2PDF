"""
ページ送りのテストツール
Kindleのページが正しく送られるかテストします
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager


def test_page_navigation():
    """ページ送りのテスト"""
    print("="*60)
    print("Kindleページ送りテストツール")
    print("="*60)
    
    # ブラウザを起動
    print("\n1. ブラウザを起動しています...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Kindle Cloud Readerを開く
    print("2. Kindle Cloud Readerを開きます...")
    driver.get("https://read.amazon.co.jp/kindle-library")
    
    print("\n" + "="*60)
    print("【操作】")
    print("1. ログインして本を開いてください")
    print("2. 本の最初のページに移動してください")
    print("3. 準備ができたらEnterキーを押してください")
    print("="*60 + "\n")
    input()
    
    # テスト実行
    print("\n3. ページ送りテストを開始します（5ページ）...\n")
    
    for i in range(1, 6):
        print(f"ページ {i}/5")
        print(f"  現在のURL: {driver.current_url}")
        
        if i < 5:
            # ページ送りを実行
            try:
                body = driver.find_element("tag name", "body")
                body.send_keys(Keys.ARROW_RIGHT)
                print(f"  → 右矢印キーを送信しました")
            except Exception as e:
                print(f"  エラー: {e}")
            
            # 待機
            print(f"  3秒待機中...")
            time.sleep(3)
            print()
    
    print("="*60)
    print("テスト完了！")
    print("各ページが正しく変わっていましたか？")
    print("="*60)
    
    input("\nEnterキーを押して終了...")
    driver.quit()


if __name__ == "__main__":
    test_page_navigation()
