#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Draft Manager - SNS投稿下書き管理ツール
txtファイルの一覧表示、プレビュー、編集、削除、移動機能を提供
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from pathlib import Path


class DraftManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Draft Manager - SNS投稿管理")
        self.root.geometry("1200x700")

        # 現在の作業ディレクトリを取得（auto_Xプロジェクトルート）
        self.project_root = Path(__file__).parent.parent.parent
        self.draft_folder = self.project_root / "sns" / "draft"
        self.sns_folder = self.project_root / "sns"

        # draft フォルダが存在しない場合は作成
        self.draft_folder.mkdir(parents=True, exist_ok=True)

        # ファイルデータを保存する辞書
        self.file_data = {}  # {file_path: {'var': BooleanVar, 'content': str, 'path': Path}}

        self.setup_ui()
        self.refresh_file_list()

    def setup_ui(self):
        """UIのセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # フォルダ選択フレーム
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(folder_frame, text="Draft フォルダ:").grid(row=0, column=0, sticky=tk.W)
        self.folder_var = tk.StringVar(value=str(self.draft_folder))
        ttk.Label(folder_frame, textvariable=self.folder_var, relief="sunken", padding="5").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        ttk.Button(folder_frame, text="参照...", command=self.select_folder).grid(row=0, column=2, padx=(5, 0))

        folder_frame.columnconfigure(1, weight=1)

        # ファイル一覧フレーム（チェックボックス、ファイル名、プレビュー）
        list_frame = ttk.LabelFrame(main_frame, text="ファイル一覧", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # スクロール可能なフレーム
        canvas = tk.Canvas(list_frame, bg="white")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # ヘッダーフレーム
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(header_frame, text="選択", font=("MS Gothic", 10, "bold")).grid(row=0, column=0, padx=(0, 20))
        ttk.Label(header_frame, text="ファイル名", font=("MS Gothic", 10, "bold")).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        ttk.Label(header_frame, text="プレビュー", font=("MS Gothic", 10, "bold")).grid(row=0, column=2, sticky=tk.W)

        header_frame.columnconfigure(1, weight=0)
        header_frame.columnconfigure(2, weight=1)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0), sticky=tk.W)

        ttk.Button(button_frame, text="更新", command=self.refresh_file_list).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="全選択", command=self.select_all).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="全選択解除", command=self.deselect_all).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="削除", command=self.delete_files).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="編集", command=self.edit_file).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="SNSへ移動", command=self.move_to_sns).grid(row=0, column=5, padx=(5, 0))

        # グリッドの重みを設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def select_folder(self):
        """フォルダ選択ダイアログ"""
        folder = filedialog.askdirectory(initialdir=self.draft_folder)
        if folder:
            self.draft_folder = Path(folder)
            self.folder_var.set(str(self.draft_folder))
            self.refresh_file_list()

    def refresh_file_list(self):
        """ファイル一覧を更新"""
        # 既存のウィジェットをクリア（ヘッダー以外）
        for widget in self.scrollable_frame.winfo_children()[1:]:  # ヘッダー（インデックス0）を残して削除
            widget.destroy()

        # ファイルデータをクリア
        self.file_data.clear()

        if not self.draft_folder.exists():
            return

        # txtファイルを取得してソート
        txt_files = sorted([f for f in self.draft_folder.glob("*.txt")])

        for i, file_path in enumerate(txt_files, 1):  # ヘッダーが0なので1からスタート
            try:
                # ファイル内容を読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # プレビュー用に最初の150文字までを取得
                preview = content[:150] + "..." if len(content) > 150 else content
                preview = preview.replace("\n", " ")  # 改行をスペースに変換

                # チェックボックス用の変数
                var = tk.BooleanVar()
                self.file_data[str(file_path)] = {
                    'var': var,
                    'content': content,
                    'path': file_path
                }

                # ファイル行フレーム
                file_frame = ttk.Frame(self.scrollable_frame)
                file_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), padx=5, pady=2)
                file_frame.columnconfigure(2, weight=1)

                # チェックボックス
                checkbox = ttk.Checkbutton(file_frame, variable=var)
                checkbox.grid(row=0, column=0, padx=(0, 20))

                # ファイル名（固定幅）
                filename_label = ttk.Label(file_frame, text=file_path.name, font=("MS Gothic", 9), width=25)
                filename_label.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)

                # プレビュー（可変幅）
                preview_label = ttk.Label(file_frame, text=preview, font=("MS Gothic", 9), foreground="gray")
                preview_label.grid(row=0, column=2, sticky=(tk.W, tk.E))

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                # エラーファイルも表示
                var = tk.BooleanVar()
                self.file_data[str(file_path)] = {
                    'var': var,
                    'content': f"[読み込みエラー: {str(e)}]",
                    'path': file_path
                }

                file_frame = ttk.Frame(self.scrollable_frame)
                file_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), padx=5, pady=2)
                file_frame.columnconfigure(2, weight=1)

                checkbox = ttk.Checkbutton(file_frame, variable=var)
                checkbox.grid(row=0, column=0, padx=(0, 20))

                filename_label = ttk.Label(file_frame, text=file_path.name, font=("MS Gothic", 9), width=25)
                filename_label.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)

                error_label = ttk.Label(file_frame, text="[読み込みエラー]", font=("MS Gothic", 9), foreground="red")
                error_label.grid(row=0, column=2, sticky=(tk.W, tk.E))

    def select_all(self):
        """全ファイルを選択"""
        for data in self.file_data.values():
            data['var'].set(True)

    def deselect_all(self):
        """全選択を解除"""
        for data in self.file_data.values():
            data['var'].set(False)

    def get_selected_files(self):
        """チェックされたファイルのパスリストを取得"""
        selected_files = []
        for file_path_str, data in self.file_data.items():
            if data['var'].get():  # チェックボックスがチェックされている場合
                selected_files.append(data['path'])
        return selected_files

    def delete_files(self):
        """チェックされたファイルを削除"""
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "削除するファイルにチェックを入れてください。")
            return

        file_names = [f.name for f in selected_files]
        if not messagebox.askyesno("確認", f"以下のファイルを削除しますか？\n\n" + "\n".join(file_names)):
            return

        try:
            for file_path in selected_files:
                file_path.unlink()
            self.refresh_file_list()
            messagebox.showinfo("完了", f"{len(selected_files)}個のファイルを削除しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル削除中にエラーが発生しました:\n{str(e)}")

    def edit_file(self):
        """チェックされたファイルを編集"""
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "編集するファイルにチェックを入れてください。")
            return

        if len(selected_files) > 1:
            messagebox.showwarning("警告", "編集は1つのファイルのみチェックしてください。")
            return

        file_path = selected_files[0]
        EditWindow(self.root, file_path, self.refresh_file_list)

    def move_to_sns(self):
        """チェックされたファイルをSNSフォルダに移動"""
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "移動するファイルにチェックを入れてください。")
            return

        file_names = [f.name for f in selected_files]
        if not messagebox.askyesno("確認", f"以下のファイルをSNSフォルダに移動しますか？\n\n" + "\n".join(file_names)):
            return

        try:
            moved_count = 0
            for file_path in selected_files:
                dest_path = self.sns_folder / file_path.name
                if dest_path.exists():
                    if messagebox.askyesno("ファイル重複", f"{file_path.name} は既に存在します。上書きしますか？"):
                        shutil.move(str(file_path), str(dest_path))
                        moved_count += 1
                else:
                    shutil.move(str(file_path), str(dest_path))
                    moved_count += 1

            self.refresh_file_list()
            messagebox.showinfo("完了", f"{moved_count}個のファイルをSNSフォルダに移動しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル移動中にエラーが発生しました:\n{str(e)}")


class EditWindow:
    """ファイル編集用ウィンドウ"""
    def __init__(self, parent, file_path, refresh_callback):
        self.file_path = file_path
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)
        self.window.title(f"編集 - {file_path.name}")
        self.window.geometry("600x400")

        self.setup_ui()
        self.load_content()

    def setup_ui(self):
        """編集ウィンドウのUIセットアップ"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # テキストエリア
        self.text_area = tk.Text(main_frame, wrap=tk.WORD, font=("MS Gothic", 10))
        text_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=text_scroll.set)

        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="保存", command=self.save_file).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="キャンセル", command=self.window.destroy).grid(row=0, column=1)

        # 文字数カウント
        self.char_count_var = tk.StringVar()
        ttk.Label(button_frame, textvariable=self.char_count_var).grid(row=0, column=2, padx=(20, 0))

        # テキスト変更時のイベント
        self.text_area.bind("<KeyRelease>", self.update_char_count)
        self.text_area.bind("<Button-1>", self.update_char_count)

        # グリッド設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

    def load_content(self):
        """ファイル内容を読み込み"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text_area.insert("1.0", content)
            self.update_char_count()
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル読み込みエラー:\n{str(e)}")
            self.window.destroy()

    def update_char_count(self, event=None):
        """文字数を更新"""
        content = self.text_area.get("1.0", "end-1c")
        char_count = len(content)
        self.char_count_var.set(f"文字数: {char_count}/280")

        # 280文字を超えた場合は赤色で表示
        if char_count > 280:
            self.char_count_var.set(f"文字数: {char_count}/280 (超過)")

    def save_file(self):
        """ファイルを保存"""
        content = self.text_area.get("1.0", "end-1c")

        # 280文字制限チェック
        if len(content) > 280:
            if not messagebox.askyesno("確認", "280文字を超えています。保存しますか？"):
                return

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("完了", "ファイルを保存しました。")
            self.refresh_callback()  # ファイル一覧を更新
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル保存エラー:\n{str(e)}")


def main():
    root = tk.Tk()
    app = DraftManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()