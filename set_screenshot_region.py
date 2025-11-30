"""
スクリーンショット領域を設定するツール
マウスで矩形領域を選択し、config.jsonを自動更新します
"""

import json
import tkinter as tk
from tkinter import messagebox
import pyautogui


class ScreenRegionSelector:
    """画面領域選択ツール"""
    
    def __init__(self):
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None
        self.root = None
        self.canvas = None
        
    def start_selection(self):
        """領域選択を開始"""
        print("="*60)
        print("スクリーンショット領域選択ツール")
        print("="*60)
        print("\n【使い方】")
        print("1. Kindleのページを開いて、キャプチャしたい状態にしてください")
        print("2. このウィンドウに戻ってEnterキーを押してください")
        print("3. 画面が半透明になるので、マウスでドラッグして領域を選択")
        print("4. マウスを離すと、選択した領域が保存されます")
        print("="*60)
        input("\n準備ができたらEnterキーを押してください...")
        
        # 全画面の透明ウィンドウを作成
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        
        # キャンバスを作成
        self.canvas = tk.Canvas(
            self.root, 
            cursor='cross',
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 説明テキスト
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            50,
            text="マウスをドラッグして領域を選択してください（ESCでキャンセル）",
            fill='white',
            font=('Arial', 20, 'bold')
        )
        
        # イベントバインド
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.root.bind('<Escape>', lambda e: self.cancel())
        
        self.root.mainloop()
    
    def on_mouse_down(self, event):
        """マウスボタンが押された"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 既存の矩形を削除
        if self.rect:
            self.canvas.delete(self.rect)
    
    def on_mouse_drag(self, event):
        """マウスがドラッグされた"""
        if self.start_x is None or self.start_y is None:
            return
        
        # 既存の矩形を削除
        if self.rect:
            self.canvas.delete(self.rect)
        
        # 新しい矩形を描画
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            event.x, event.y,
            outline='red',
            width=3
        )
        
        # 座標情報を表示
        width = abs(event.x - self.start_x)
        height = abs(event.y - self.start_y)
        info_text = f"開始: ({self.start_x}, {self.start_y}) | 現在: ({event.x}, {event.y}) | サイズ: {width} x {height}"
        
        # 既存の情報テキストを削除して新しく作成
        self.canvas.delete('info')
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            self.root.winfo_screenheight() - 50,
            text=info_text,
            fill='yellow',
            font=('Arial', 16),
            tags='info'
        )
    
    def on_mouse_up(self, event):
        """マウスボタンが離された"""
        self.end_x = event.x
        self.end_y = event.y
        
        # 座標を正規化（左上が小さい値になるように）
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        width = x2 - x1
        height = y2 - y1
        
        # 領域が小さすぎる場合は無視
        if width < 10 or height < 10:
            messagebox.showwarning("警告", "選択領域が小さすぎます。もう一度選択してください。")
            self.rect = None
            return
        
        # 確認ダイアログ
        message = f"選択した領域:\n\n"
        message += f"位置: ({x1}, {y1})\n"
        message += f"サイズ: {width} x {height}\n\n"
        message += f"この領域でconfig.jsonを更新しますか？"
        
        if messagebox.askyesno("確認", message):
            self.save_to_config(x1, y1, width, height)
            self.root.destroy()
        else:
            # もう一度選択
            self.rect = None
            self.start_x = None
            self.start_y = None
    
    def cancel(self):
        """キャンセル"""
        if messagebox.askyesno("確認", "領域選択をキャンセルしますか？"):
            self.root.destroy()
    
    def save_to_config(self, x, y, width, height):
        """config.jsonに保存"""
        config_path = "config.json"
        
        try:
            # config.jsonを読み込む
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # screenshot_regionを更新
            config['screenshot_region'] = [x, y, width, height]
            
            # config.jsonに書き込む
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print("\n" + "="*60)
            print("✓ config.jsonを更新しました！")
            print("="*60)
            print(f"\n設定された領域:")
            print(f"  位置: ({x}, {y})")
            print(f"  サイズ: {width} x {height}")
            print(f"\nconfig.jsonの内容:")
            print(f'  "screenshot_region": [{x}, {y}, {width}, {height}]')
            print("\nこれでkindle_to_pdf.pyを実行すると、")
            print("選択した領域のみがキャプチャされます。")
            print("="*60)
            
            messagebox.showinfo(
                "完了", 
                f"config.jsonを更新しました！\n\n"
                f"領域: [{x}, {y}, {width}, {height}]\n\n"
                f"kindle_to_pdf.pyを実行してください。"
            )
            
        except FileNotFoundError:
            print(f"\nエラー: {config_path} が見つかりません。")
            messagebox.showerror("エラー", f"{config_path} が見つかりません。")
        except Exception as e:
            print(f"\nエラー: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました:\n{e}")


def show_current_mouse_position():
    """現在のマウス位置を表示するツール"""
    print("\n【マウス位置確認モード】")
    print("マウスを動かすと、現在の座標が表示されます。")
    print("Ctrl+C で終了します。\n")
    
    try:
        while True:
            x, y = pyautogui.position()
            position_str = f"X: {x:4d} Y: {y:4d}"
            print(position_str, end='\r')
    except KeyboardInterrupt:
        print("\n\n終了しました。")


def main():
    """メイン関数"""
    print("\n" + "="*60)
    print("スクリーンショット領域設定ツール")
    print("="*60)
    print("\nモードを選択してください:")
    print("1. 矩形領域を選択してconfig.jsonを更新（推奨）")
    print("2. マウス位置を確認（座標を手動でメモする場合）")
    print("="*60)
    
    choice = input("\n選択 (1 or 2): ").strip()
    
    if choice == "1":
        selector = ScreenRegionSelector()
        selector.start_selection()
    elif choice == "2":
        show_current_mouse_position()
    else:
        print("無効な選択です。1 または 2 を入力してください。")


if __name__ == "__main__":
    main()
