"""
フォルダ内の画像ファイルをPDFに変換するスクリプト
"""

import os
import glob
import json
from datetime import datetime
import img2pdf


def load_config(config_path="config.json"):
    """設定ファイルを読み込む"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"警告: 設定ファイル '{config_path}' が見つかりません。デフォルト設定を使用します。")
        return {}


def get_image_files(image_dir):
    """指定ディレクトリから画像ファイルを取得"""
    # PNG画像を取得（page_0001.png, page_0002.png...の形式）
    pattern = os.path.join(image_dir, "page_*.png")
    image_files = sorted(glob.glob(pattern))
    
    if not image_files:
        # 他の画像形式も試す
        patterns = [
            os.path.join(image_dir, "*.png"),
            os.path.join(image_dir, "*.jpg"),
            os.path.join(image_dir, "*.jpeg")
        ]
        for pattern in patterns:
            image_files = sorted(glob.glob(pattern))
            if image_files:
                break
    
    return image_files


def create_pdf(image_files, output_filename=None, delete_images=False):
    """
    画像ファイルからPDFを作成
    
    Args:
        image_files (list): 画像ファイルのパスリスト
        output_filename (str): 出力PDFファイル名
        delete_images (bool): PDF作成後に画像を削除するか
    """
    if not image_files:
        print("エラー: 画像ファイルが見つかりません")
        return False
    
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"kindle_book_{timestamp}.pdf"
    
    print(f"\nPDFを作成しています: {output_filename}")
    print(f"画像ファイル数: {len(image_files)}")
    
    try:
        # 画像をPDFに変換
        with open(output_filename, "wb") as f:
            f.write(img2pdf.convert(image_files))
        
        print(f"✓ PDF作成完了: {output_filename}")
        
        # 画像ファイルを削除（オプション）
        if delete_images:
            print("\n画像ファイルを削除しています...")
            for img_path in image_files:
                try:
                    os.remove(img_path)
                    print(f"  削除: {os.path.basename(img_path)}")
                except Exception as e:
                    print(f"  警告: {os.path.basename(img_path)} の削除に失敗: {e}")
            print("✓ 画像ファイルの削除完了")
        
        return True
        
    except Exception as e:
        print(f"✗ PDFの作成中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン処理"""
    print("="*60)
    print("画像からPDF作成ツール")
    print("="*60)
    print()
    
    # 設定を読み込む
    config = load_config()
    
    # 画像ディレクトリ
    image_dir = config.get("output_dir", "data")
    
    # PDF作成後に画像を削除するか
    delete_images = config.get("delete_screenshots", False)
    
    # 出力PDFファイル名
    pdf_filename = config.get("pdf_filename", None)
    
    print(f"画像ディレクトリ: {image_dir}")
    
    # ディレクトリが存在するか確認
    if not os.path.exists(image_dir):
        print(f"\nエラー: ディレクトリが見つかりません: {image_dir}")
        print("スクリーンショットを撮影してから実行してください。")
        input("\nEnterキーを押して終了...")
        return
    
    # 画像ファイルを取得
    print(f"\n画像ファイルを検索中...")
    image_files = get_image_files(image_dir)
    
    if not image_files:
        print(f"\nエラー: {image_dir} に画像ファイルが見つかりません")
        print("スクリーンショットを撮影してから実行してください。")
        input("\nEnterキーを押して終了...")
        return
    
    print(f"✓ {len(image_files)}個の画像ファイルを検出")
    print(f"  最初: {os.path.basename(image_files[0])}")
    print(f"  最後: {os.path.basename(image_files[-1])}")
    
    # PDF作成の確認
    print(f"\n{'='*60}")
    if delete_images:
        print("⚠️  警告: PDF作成後、元の画像ファイルは削除されます")
    print(f"{'='*60}")
    response = input("\nPDFを作成しますか？ (y/n): ").strip().lower()
    
    if response != 'y':
        print("キャンセルしました。")
        return
    
    # PDFを作成
    success = create_pdf(image_files, pdf_filename, delete_images)
    
    if success:
        print(f"\n{'='*60}")
        print("✓ 処理が正常に完了しました！")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("✗ エラーが発生しました")
        print(f"{'='*60}")
    
    input("\nEnterキーを押して終了...")


if __name__ == "__main__":
    main()
