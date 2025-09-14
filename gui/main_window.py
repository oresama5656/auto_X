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
from .git_manager import GitManager


class MainWindow:
    """メインGUIウィンドウクラス"""
    
    def __init__(self):
        """メインウィンドウを初期化"""
        self.root = tk.Tk()
        self.git_manager = GitManager()
        self._setup_window()
        self._create_tabs()
        self._setup_menu()

        # GUI起動時に自動pull実行
        self._auto_pull_on_startup()
        
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

    def _auto_pull_on_startup(self):
        """GUI起動時の自動pull処理"""
        # Git利用可能性をチェック
        if not self.git_manager.is_git_available():
            return  # Gitが使えない場合は静かにスキップ

        if not self.git_manager.check_git_status():
            return  # Gitリポジトリでない場合もスキップ

        # プログレスダイアログを作成
        progress_dialog = self._create_pull_progress_dialog()

        def on_pull_progress(message):
            """Pull進行状況更新"""
            self.root.after(0, lambda: progress_dialog.update_status(message))

        def on_pull_completion(success, message):
            """Pull完了処理"""
            self.root.after(0, lambda: self._on_pull_completion(success, message, progress_dialog))

        # 自動pullを実行
        self.git_manager.pull_from_remote(
            progress_callback=on_pull_progress,
            completion_callback=on_pull_completion
        )

    def _create_pull_progress_dialog(self):
        """Pull用プログレスダイアログ作成"""
        class PullProgressDialog:
            def __init__(self, parent):
                self.window = tk.Toplevel(parent)
                self.window.title("同期中")
                self.window.geometry("300x100")
                self.window.resizable(False, False)
                self.window.transient(parent)
                self.window.grab_set()

                # センタリング
                self.window.geometry("+%d+%d" % (parent.winfo_rootx() + 150, parent.winfo_rooty() + 150))

                # ラベル
                self.status_label = ttk.Label(self.window, text="最新情報を確認中...", font=("Arial", 10))
                self.status_label.pack(pady=20)

                # プログレスバー
                self.progress = ttk.Progressbar(self.window, mode='indeterminate')
                self.progress.pack(pady=10, padx=20, fill='x')
                self.progress.start()

            def update_status(self, message):
                self.status_label.config(text=message)
                self.window.update()

            def close(self):
                self.progress.stop()
                self.window.destroy()

        return PullProgressDialog(self.root)

    def _on_pull_completion(self, success, message, progress_dialog):
        """Pull完了時の処理"""
        progress_dialog.close()

        if success:
            # 成功時は控えめに表示（ステータスバーがあれば理想的）
            if "既に最新状態" not in message:
                # 更新があった場合のみ通知
                self.root.title(f"auto_X - {message}")
                # 2秒後にタイトルを元に戻す
                self.root.after(2000, lambda: self.root.title("auto_X - X (Twitter) 自動投稿システム"))
        else:
            # エラー時は明確に表示
            messagebox.showwarning(
                "同期エラー",
                f"最新情報の取得に失敗しました:\n{message}\n\n"
                "オフライン環境またはネットワークエラーの可能性があります。\n"
                "手動で同期するか、ネットワーク接続を確認してください。"
            )
    
    def refresh_all(self):
        """全タブのデータを更新（他のタブから呼び出し用）"""
        try:
            if hasattr(self, 'post_tab'):
                self.post_tab.refresh_files()
        except Exception as e:
            messagebox.showerror("更新エラー", f"データ更新に失敗しました: {e}")