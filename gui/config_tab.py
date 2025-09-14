# -*- coding: utf-8 -*-
"""
設定タブ

configs/sns.json の設定を GUI で編集
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from .utils import (
    load_config, save_config, parse_post_time, parse_fixed_times, 
    format_fixed_times, validate_time_format
)
from .workflow_optimizer import (
    optimize_cron_for_times, update_workflow_cron, get_execution_frequency_info
)
from .git_manager import GitManager


class ConfigTab:
    """設定タブクラス"""
    
    def __init__(self, parent):
        """
        設定タブを初期化
        
        Args:
            parent: 親ウィジェット（通常はNotebook）
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
        # 設定データ
        self.config = {}
        
        # Git管理オブジェクト
        self.git_manager = GitManager()
        
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム（スクロール対応）
        self.main_frame = ttk.Frame(self.frame)
        
        # === 投稿時刻設定セクション ===
        self.times_section = ttk.LabelFrame(self.main_frame, text="投稿時刻設定")
        
        # 投稿時刻（カンマ区切り）
        ttk.Label(self.times_section, text="投稿時刻:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.times_var = tk.StringVar()
        self.times_entry = ttk.Entry(self.times_section, textvariable=self.times_var, width=50)
        self.times_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(self.times_section, text="例: 09:00,12:00,15:00,18:00,21:00", font=("Arial", 8), foreground="gray").grid(row=1, column=1, sticky='w', padx=5)
        
        # 即投稿テスト用の例
        ttk.Label(self.times_section, text="即投稿テスト用:", font=("Arial", 8), foreground="blue").grid(row=2, column=1, sticky='w', padx=5)
        ttk.Label(self.times_section, text="15:01,15:02,15:03 (1分間隔で3回)", font=("Arial", 8), foreground="gray").grid(row=3, column=1, sticky='w', padx=5)
        
        # === 共通設定セクション ===
        self.common_section = ttk.LabelFrame(self.main_frame, text="共通設定")
        
        # startDate
        ttk.Label(self.common_section, text="開始日:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(self.common_section, textvariable=self.start_date_var, width=15)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(self.common_section, text="例: auto または 2025-09-12", font=("Arial", 8), foreground="gray").grid(row=0, column=2, sticky='w', padx=5)
        
        # skipWeekends
        self.skip_weekends_var = tk.BooleanVar()
        self.skip_weekends_check = ttk.Checkbutton(
            self.common_section,
            text="週末をスキップ",
            variable=self.skip_weekends_var
        )
        self.skip_weekends_check.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        # === 操作ボタンセクション ===
        self.button_section = ttk.Frame(self.main_frame)
        
        # 保存ボタン
        self.save_button = ttk.Button(
            self.button_section,
            text="保存",
            command=self.save_config,
            width=15
        )
        
        # GitHub反映ボタン
        self.push_to_github_button = ttk.Button(
            self.button_section,
            text="GitHubに反映",
            command=self.push_to_github,
            width=15,
            style="Accent.TButton"
        )
        
        # 読み込みボタン
        self.load_button = ttk.Button(
            self.button_section,
            text="再読み込み",
            command=self.load_config,
            width=15
        )
        
        # 実行頻度表示
        self.frequency_frame = ttk.Frame(self.main_frame)
        self.frequency_label = ttk.Label(
            self.frequency_frame,
            text="GitHub Actions実行頻度: 未計算",
            font=("Arial", 9),
            foreground="blue"
        )
        
        # === ステータスセクション ===
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_label = ttk.Label(
            self.status_frame,
            text="設定ファイル: 未読み込み",
            font=("Arial", 9)
        )
        
    def _setup_layout(self):
        """レイアウトを設定"""
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 投稿時刻設定
        self.times_section.pack(fill='x', pady=(0, 10))
        
        # 共通設定
        self.common_section.pack(fill='x', pady=(0, 10))
        
        # ボタン
        self.button_section.pack(fill='x', pady=(0, 10))
        self.load_button.pack(side='left', padx=(0, 10))
        self.save_button.pack(side='left', padx=(0, 10))
        self.push_to_github_button.pack(side='left')
        
        # 実行頻度表示
        self.frequency_frame.pack(fill='x', pady=(0, 10))
        self.frequency_label.pack(side='left')
        
        # ステータス
        self.status_frame.pack(fill='x')
        self.status_label.pack(side='left')
        
    def _bind_events(self):
        """イベントをバインド"""
        # 時刻入力変更時に実行頻度を更新
        self.times_var.trace_add('write', self._on_times_change)
    
    def _on_times_change(self, *args):
        """時刻設定変更時の処理"""
        self.update_frequency_display()
    
    def load_config(self):
        """設定ファイルを読み込んでGUIに反映"""
        try:
            self.config = load_config()
            posting = self.config.get('posting', {})
            
            # 投稿時刻設定（backward compatibility）
            times = posting.get('times') or posting.get('fixedTimes', [])
            self.times_var.set(format_fixed_times(times))
            
            # 共通設定
            self.start_date_var.set(posting.get('startDate', 'auto'))
            self.skip_weekends_var.set(posting.get('skipWeekends', False))
            
            # ステータス更新
            self.status_label.config(text="設定ファイル: 読み込み完了", foreground="green")
            
            # 実行頻度表示を更新
            self.update_frequency_display()
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの読み込みに失敗しました:\n{str(e)}")
            self.status_label.config(text=f"エラー: {str(e)}", foreground="red")
    
    def save_config(self):
        """GUI設定を設定ファイルに保存"""
        try:
            # 入力値の検証
            if not self._validate_inputs():
                return
            
            # 設定を構築
            if not self.config:
                # 基本構造を作成
                self.config = {
                    "posting": {},
                    "twitterApi": {
                        "apiKey": "",
                        "apiKeySecret": "",
                        "accessToken": "",
                        "accessTokenSecret": ""
                    }
                }
            
            posting = self.config['posting']
            
            # 設定構築
            posting['use'] = True
            posting['times'] = parse_fixed_times(self.times_var.get())
            posting['startDate'] = self.start_date_var.get().strip() or 'auto'
            posting['skipWeekends'] = self.skip_weekends_var.get()
            
            # 旧設定項目をクリア
            posting.pop('scheduleType', None)
            posting.pop('interval', None) 
            posting.pop('postTime', None)
            posting.pop('autoTimeOffset', None)
            posting.pop('fixedTimes', None)
            
            # 設定ファイルに保存
            save_config(self.config)
            
            # ステータス更新
            self.status_label.config(text="設定ファイル: 保存完了", foreground="blue")
            messagebox.showinfo("保存完了", "設定を保存しました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました:\n{str(e)}")
            self.status_label.config(text=f"保存エラー: {str(e)}", foreground="red")
    
    def _validate_inputs(self) -> bool:
        """入力値の検証"""
        try:
            # 投稿時刻の検証
            times_str = self.times_var.get().strip()
            if not times_str:
                messagebox.showerror("入力エラー", "投稿時刻を入力してください。")
                return False
            
            times_list = parse_fixed_times(times_str)
            if not times_list:
                messagebox.showerror("入力エラー", "少なくとも1つの投稿時刻を入力してください。")
                return False
            
            for time_str in times_list:
                if not validate_time_format(time_str):
                    messagebox.showerror("入力エラー", f"無効な時刻形式: {time_str}\nHH:MM形式で入力してください。")
                    return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("入力エラー", f"数値の形式が正しくありません: {e}")
            return False
    
    def push_to_github(self):
        """設定をGitHubに反映（保存＋最適化＋Git操作）"""
        try:
            # Git利用可能性確認
            if not self.git_manager.is_git_available():
                messagebox.showerror("エラー", "Gitが利用できません。\nGitがインストールされているか確認してください。")
                return
            
            if not self.git_manager.check_git_status():
                messagebox.showerror("エラー", "Gitリポジトリではありません。\nGitが初期化されているか確認してください。")
                return
            
            # まず設定保存
            self.save_config()
            
            # GitHub Actions最適化
            times_list = parse_fixed_times(self.times_var.get())
            workflow_updated = update_workflow_cron(times_list)
            
            # 変更対象ファイル
            files_to_commit = ['configs/sns.json']
            if workflow_updated:
                files_to_commit.append('.github/workflows/sns.yml')
            
            # コミットメッセージ生成
            commit_msg = self.git_manager.generate_commit_message(files_to_commit)
            
            # 進行状況ダイアログ
            progress_dialog = self._create_progress_dialog()
            
            def on_progress(message):
                """進行状況更新"""
                self.frame.after(0, lambda: progress_dialog.update_status(message))
            
            def on_completion(success, message):
                """完了処理"""
                self.frame.after(0, lambda: self._on_git_completion(success, message, progress_dialog, workflow_updated, times_list))
            
            # バックグラウンドでGit操作実行
            self.git_manager.commit_and_push(
                files_to_commit,
                commit_msg,
                on_progress,
                on_completion
            )
            
        except Exception as e:
            messagebox.showerror("エラー", f"GitHub反映処理でエラーが発生しました:\n{str(e)}")
    
    def _create_progress_dialog(self):
        """進行状況ダイアログを作成"""
        class ProgressDialog:
            def __init__(self, parent):
                self.window = tk.Toplevel(parent)
                self.window.title("GitHub反映中...")
                self.window.geometry("400x150")
                self.window.resizable(False, False)
                self.window.transient(parent)
                self.window.grab_set()
                
                # センタリング
                self.window.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
                
                # ラベル
                self.status_label = ttk.Label(self.window, text="準備中...", font=("Arial", 10))
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
        
        return ProgressDialog(self.frame.winfo_toplevel())
    
    def _on_git_completion(self, success, message, progress_dialog, workflow_updated, times_list):
        """Git操作完了時の処理"""
        progress_dialog.close()
        
        if success:
            # 成功メッセージ
            details = []
            details.append("✅ 設定ファイル保存")
            
            if workflow_updated:
                freq_info = get_execution_frequency_info(times_list)
                savings = freq_info.get('savings_percent', 0)
                details.append("✅ GitHub Actions最適化")
                details.append(f"   実行頻度: {freq_info['description']}")
                details.append(f"   リソース削減: {savings}%")
            
            details.append("✅ GitHubに反映完了")
            
            messagebox.showinfo("完了", f"{message}\n\n" + "\n".join(details))
            
            # 表示更新
            self.update_frequency_display()
            
        else:
            messagebox.showerror("エラー", message)
    
    def update_frequency_display(self):
        """実行頻度表示を更新"""
        try:
            times_str = self.times_var.get().strip()
            if times_str:
                times_list = parse_fixed_times(times_str)
                freq_info = get_execution_frequency_info(times_list)
                
                savings = freq_info.get('savings_percent', 0)
                display_text = f"GitHub Actions実行頻度: {freq_info['description']} (削減: {savings}%)"
                
                if savings > 50:
                    color = "green"
                elif savings > 0:
                    color = "orange"
                else:
                    color = "red"
                    
                self.frequency_label.config(text=display_text, foreground=color)
            else:
                self.frequency_label.config(text="GitHub Actions実行頻度: 未設定", foreground="gray")
                
        except Exception:
            self.frequency_label.config(text="GitHub Actions実行頻度: エラー", foreground="red")