# -*- coding: utf-8 -*-
"""
メインウィンドウクラス

タブ構成のGUIメインウィンドウ
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

from .post_tab import PostTab
from .config_tab import ConfigTab


class MainWindow:
    """メインGUIウィンドウクラス"""
    
    def __init__(self):
        """メインウィンドウを初期化"""
        self.root = tk.Tk()
        self._setup_window()
        self._create_tabs()
        self._setup_menu()
        
    def _setup_window(self):
        """ウィンドウの基本設定"""
        self.root.title("auto_X - X (Twitter) 自動投稿システム")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        # アイコン設定（将来的に追加可能）
        # self.root.iconbitmap('icon.ico')
        
        # 終了時の処理
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _create_tabs(self):
        """タブの作成と配置"""
        # ノートブック（タブコンテナ）を作成
        self.notebook = ttk.Notebook(self.root)
        
        # 投稿管理タブを作成
        try:
            self.post_tab = PostTab(self.notebook)
            self.notebook.add(self.post_tab.frame, text="投稿管理")
        except Exception as e:
            messagebox.showerror("エラー", f"投稿管理タブの作成に失敗しました: {e}")
            
        # 設定タブを作成
        try:
            self.config_tab = ConfigTab(self.notebook)
            self.notebook.add(self.config_tab.frame, text="設定")
        except Exception as e:
            messagebox.showerror("エラー", f"設定タブの作成に失敗しました: {e}")
            
        # ノートブックを配置
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
    def _setup_menu(self):
        """メニューバーの設定（将来の拡張用）"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self._on_closing)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="バージョン情報", command=self._show_about)
        
    def _show_about(self):
        """バージョン情報ダイアログ"""
        messagebox.showinfo(
            "バージョン情報",
            "auto_X GUI v1.0.0\n\n"
            "X (Twitter) 自動投稿システムのGUIツール\n"
            "GitHub Actions連携による自動投稿を支援"
        )
        
    def _on_closing(self):
        """ウィンドウ閉じる時の処理"""
        try:
            # 未保存の変更があるかチェック（将来的に実装）
            if hasattr(self, 'config_tab'):
                # 設定タブに未保存の変更があるかチェック
                pass
                
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            print(f"終了処理でエラー: {e}", file=sys.stderr)
            # 強制終了
            sys.exit(0)
    
    def run(self):
        """GUIアプリケーションを開始"""
        try:
            # 初回データ読み込み
            self._initial_load()
            
            # メインループ開始
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\n中断されました。")
            self._on_closing()
        except Exception as e:
            messagebox.showerror("予期しないエラー", f"アプリケーション実行中にエラーが発生しました:\n{str(e)}")
            print(f"実行エラー: {e}", file=sys.stderr)
            
    def _initial_load(self):
        """初回データ読み込み"""
        try:
            # 投稿管理タブのデータ読み込み
            if hasattr(self, 'post_tab'):
                self.post_tab.refresh_files()
                
            # 設定タブのデータ読み込み
            if hasattr(self, 'config_tab'):
                self.config_tab.load_config()
                
        except Exception as e:
            messagebox.showwarning(
                "初期化警告", 
                f"データの初期読み込みで問題が発生しました:\n{str(e)}\n\n"
                "続行しますが、正常に動作しない可能性があります。"
            )
    
    def refresh_all(self):
        """全タブのデータを更新（他のタブから呼び出し用）"""
        try:
            if hasattr(self, 'post_tab'):
                self.post_tab.refresh_files()
        except Exception as e:
            messagebox.showerror("更新エラー", f"データ更新に失敗しました: {e}")