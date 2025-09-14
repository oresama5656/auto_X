# -*- coding: utf-8 -*-
"""
投稿管理タブ

sns/ディレクトリの投稿待ちファイルを管理
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List

import subprocess
import threading
import datetime
from .utils import get_sns_files


class PostTab:
    """投稿管理タブクラス"""
    
    def __init__(self, parent):
        """
        投稿管理タブを初期化
        
        Args:
            parent: 親ウィジェット（通常はNotebook）
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        # 上部フレーム（ボタン等）
        self.top_frame = ttk.Frame(self.frame)
        
        # 更新ボタン
        self.refresh_button = ttk.Button(
            self.top_frame,
            text="更新",
            command=self.refresh_files,
            width=10
        )
        
        # スケジュール確認ボタン（API不要）
        self.plan_button = ttk.Button(
            self.top_frame,
            text="スケジュール確認",
            command=self.show_schedule,
            width=15
        )
        
        # ファイルリストフレーム
        self.list_frame = ttk.Frame(self.frame)
        
        # ファイルリスト（リストボックス + スクロールバー）
        self.files_listbox = tk.Listbox(
            self.list_frame,
            font=("Consolas", 10),  # 等幅フォント
            selectmode=tk.SINGLE,
            height=8  # 高さを制限してプレビューエリア用スペース確保
        )
        
        # プレビューフレーム
        self.preview_frame = ttk.LabelFrame(self.frame, text="ファイルプレビュー")
        
        # プレビューテキストエリア
        self.preview_text = tk.Text(
            self.preview_frame,
            height=4,
            wrap=tk.WORD,
            font=("Arial", 10),
            state=tk.DISABLED,
            bg="#f8f9fa"
        )
        
        # プレビュースクロールバー
        self.preview_scrollbar = ttk.Scrollbar(
            self.preview_frame,
            orient="vertical",
            command=self.preview_text.yview
        )
        self.preview_text.config(yscrollcommand=self.preview_scrollbar.set)
        
        # ログフレーム
        self.log_frame = ttk.LabelFrame(self.frame, text="実行ログ")
        
        # ログテキストエリア
        self.log_text = tk.Text(
            self.log_frame,
            height=6,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state=tk.DISABLED,
            bg="#2d3748",
            fg="#e2e8f0"
        )
        
        # ログスクロールバー
        self.log_scrollbar = ttk.Scrollbar(
            self.log_frame,
            orient="vertical",
            command=self.log_text.yview
        )
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)
        
        # スクロールバー
        self.scrollbar = ttk.Scrollbar(
            self.list_frame,
            orient="vertical",
            command=self.files_listbox.yview
        )
        self.files_listbox.config(yscrollcommand=self.scrollbar.set)
        
        # ステータスフレーム
        self.status_frame = ttk.Frame(self.frame)
        
        # ステータスラベル
        self.status_label = ttk.Label(
            self.status_frame,
            text="投稿待ちファイル: 0件",
            font=("Arial", 9)
        )
        
        # 情報ラベル（使用方法のヒント）
        self.info_label = ttk.Label(
            self.status_frame,
            text="※ sns/ディレクトリの*.txtファイルを表示（README.txt、posted/内は除外）",
            font=("Arial", 8),
            foreground="gray"
        )
        
    def _setup_layout(self):
        """レイアウトを設定"""
        # 上部フレームのレイアウト
        self.top_frame.pack(fill='x', padx=5, pady=(5, 0))
        self.refresh_button.pack(side='left')
        self.plan_button.pack(side='left', padx=(10, 0))
        
        # ファイルリストフレームのレイアウト
        self.list_frame.pack(fill='x', padx=5, pady=5)
        self.files_listbox.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # プレビューフレームのレイアウト
        self.preview_frame.pack(fill='x', padx=5, pady=(0, 5))
        self.preview_text.pack(side='left', fill='both', expand=True)
        self.preview_scrollbar.pack(side='right', fill='y')
        
        # ログフレームのレイアウト
        self.log_frame.pack(fill='both', expand=True, padx=5, pady=(0, 5))
        self.log_text.pack(side='left', fill='both', expand=True)
        self.log_scrollbar.pack(side='right', fill='y')
        
        # ステータスフレームのレイアウト
        self.status_frame.pack(fill='x', padx=5, pady=(0, 5))
        self.status_label.pack(side='left')
        self.info_label.pack(side='left', padx=(20, 0))
        
    def refresh_files(self):
        """ファイルリストを更新"""
        try:
            # 既存のリストをクリア
            self.files_listbox.delete(0, tk.END)
            
            # sns/ディレクトリから投稿待ちファイルを取得
            files = get_sns_files()
            
            # リストボックスに追加（昇順でソート済み）
            for file_name in files:
                self.files_listbox.insert(tk.END, file_name)
            
            # ステータスを更新
            self._update_status(len(files))
            
        except Exception as e:
            messagebox.showerror("エラー", f"ファイルリストの更新に失敗しました:\n{str(e)}")
            self._update_status(0, f"エラー: {str(e)}")
    
    def _update_status(self, file_count: int, error_msg: str = None):
        """ステータス表示を更新"""
        if error_msg:
            self.status_label.config(text=error_msg, foreground="red")
        else:
            self.status_label.config(
                text=f"投稿待ちファイル: {file_count}件",
                foreground="black"
            )
    
    def get_selected_file(self) -> str:
        """選択されているファイル名を取得"""
        try:
            selection = self.files_listbox.curselection()
            if selection:
                return self.files_listbox.get(selection[0])
            return None
        except tk.TclError:
            return None
    
    def _bind_events(self):
        """イベントバインド"""
        # ファイル選択時のプレビュー更新
        self.files_listbox.bind('<<ListboxSelect>>', self._on_file_select)
        
    def _on_file_select(self, event):
        """ファイル選択時の処理"""
        self.update_preview()
    
    def update_preview(self):
        """プレビューを更新"""
        selected_file = self.get_selected_file()
        if not selected_file:
            self._clear_preview()
            return
            
        try:
            # ファイルの内容を読み込み
            file_path = Path.cwd() / 'sns' / selected_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # プレビューに表示
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete(1.0, tk.END)
                self.preview_text.insert(1.0, content)
                
                # 文字数表示
                char_count = len(content)
                color = "red" if char_count > 280 else "green"
                self.preview_text.insert(tk.END, f"\n\n--- 文字数: {char_count}/280 ---")
                self.preview_text.tag_add("char_count", f"end-2l", "end")
                self.preview_text.tag_config("char_count", foreground=color, font=("Arial", 8))
                
                self.preview_text.config(state=tk.DISABLED)
            else:
                self._clear_preview("ファイルが見つかりません")
                
        except Exception as e:
            self._clear_preview(f"エラー: {str(e)}")
    
    def _clear_preview(self, message="ファイルを選択してください"):
        """プレビューをクリア"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, message)
        self.preview_text.config(state=tk.DISABLED)
    
    def log_message(self, message, level="INFO"):
        """ログにメッセージを追加"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_line)
        
        # 色付け
        if level == "ERROR":
            self.log_text.tag_add("error", f"end-2l", "end-1l")
            self.log_text.tag_config("error", foreground="#ff6b6b")
        elif level == "SUCCESS":
            self.log_text.tag_add("success", f"end-2l", "end-1l")
            self.log_text.tag_config("success", foreground="#51cf66")
        elif level == "WARNING":
            self.log_text.tag_add("warning", f"end-2l", "end-1l")
            self.log_text.tag_config("warning", foreground="#ffd93d")
        
        # 最新行にスクロール
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show_schedule(self):
        """スケジュール確認（API不要）"""
        self.log_message("=== スケジュール確認開始 ===")

        # ボタンを一時無効化
        self.plan_button.config(state='disabled')

        def run_plan():
            try:
                # npm run plan 実行（API不要）
                process = subprocess.Popen(
                    "npm run plan",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )

                # リアルタイム出力
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self._add_log_safely(output.strip())

                # エラー出力を取得
                stderr_output = process.stderr.read()
                if stderr_output:
                    self._add_log_safely(stderr_output.strip(), "ERROR")

                # 結果判定
                return_code = process.poll()
                if return_code == 0:
                    self._add_log_safely("スケジュール確認が完了しました", "SUCCESS")
                    self._add_log_safely("実際の投稿はGitHub Actionsで行ってください", "INFO")
                else:
                    self._add_log_safely(f"スケジュール確認が失敗しました (終了コード: {return_code})", "ERROR")

            except Exception as e:
                self._add_log_safely(f"実行エラー: {str(e)}", "ERROR")
            finally:
                # ボタンを有効化
                self.frame.after(0, self._enable_buttons)

        # スレッドで実行
        thread = threading.Thread(target=run_plan, daemon=True)
        thread.start()

    def _add_log_safely(self, message, level="INFO"):
        """スレッドセーフなログ追加"""
        self.frame.after(0, lambda: self.log_message(message, level))

    def _enable_buttons(self):
        """ボタンを有効化"""
        self.plan_button.config(state='normal')