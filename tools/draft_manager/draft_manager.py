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
import json
from datetime import datetime
from pathlib import Path


class DraftManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Draft Manager - SNS投稿管理")
        self.root.geometry("900x600")

        # 現在の作業ディレクトリを取得（auto_Xプロジェクトルート）
        self.project_root = Path(__file__).parent.parent.parent
        self.draft_folder = self.project_root / "sns" / "draft"
        self.sns_folder = self.project_root / "sns"
        self.last_number_file = self.project_root / "last_number.json"

        # draft フォルダが存在しない場合は作成
        self.draft_folder.mkdir(parents=True, exist_ok=True)

        # ファイルデータを保存するリスト（Listbox用）
        self.file_list = []  # [{'path': Path, 'name': str, 'content': str}, ...]

        # 元の並び順を保存（リセット用）
        self.original_file_order = []

        # プレビュー設定
        self.preview_length = 80  # プレビュー表示文字数

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

        # === Draft一覧とプレビュー ===
        draft_frame = ttk.LabelFrame(main_frame, text="Draft ファイル一覧", padding="5")
        draft_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Draft ファイル用Listbox
        draft_list_frame = ttk.Frame(draft_frame)
        draft_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.draft_listbox = tk.Listbox(draft_list_frame, selectmode=tk.EXTENDED, font=("MS Gothic", 9))
        draft_scroll = ttk.Scrollbar(draft_list_frame, orient="vertical", command=self.draft_listbox.yview)
        self.draft_listbox.configure(yscrollcommand=draft_scroll.set)

        self.draft_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        draft_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 順序操作ボタン
        order_button_frame = ttk.Frame(draft_frame)
        order_button_frame.grid(row=1, column=0, pady=(10, 0))

        ttk.Button(order_button_frame, text="↑ 上へ", command=self.move_up, width=8).grid(row=0, column=0, padx=2)
        ttk.Button(order_button_frame, text="↓ 下へ", command=self.move_down, width=8).grid(row=0, column=1, padx=2)
        ttk.Button(order_button_frame, text="リセット", command=self.reset_order, width=8).grid(row=0, column=2, padx=(10, 0))


        # === 下部ボタンフレーム ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))

        # 左側ボタン（Draft操作）
        left_buttons = ttk.Frame(button_frame)
        left_buttons.grid(row=0, column=0, sticky=tk.W)

        ttk.Button(left_buttons, text="更新", command=self.refresh_file_list).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(left_buttons, text="全選択", command=self.select_all).grid(row=0, column=1, padx=5)
        ttk.Button(left_buttons, text="全選択解除", command=self.deselect_all).grid(row=0, column=2, padx=5)
        ttk.Button(left_buttons, text="削除", command=self.delete_files).grid(row=0, column=3, padx=5)
        ttk.Button(left_buttons, text="編集", command=self.edit_file).grid(row=0, column=4, padx=5)

        # 右側ボタン（SNS移行）
        right_buttons = ttk.Frame(button_frame)
        right_buttons.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))

        ttk.Button(right_buttons, text="SNSへ移動", command=self.move_to_sns, style="Accent.TButton").grid(row=0, column=0)

        button_frame.columnconfigure(1, weight=1)

        # グリッドの重みを設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Draft フレーム
        draft_frame.columnconfigure(0, weight=1)
        draft_frame.rowconfigure(0, weight=1)  # Listbox
        draft_list_frame.columnconfigure(0, weight=1)
        draft_list_frame.rowconfigure(0, weight=1)

        # ルート
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
        # Listboxをクリア
        self.draft_listbox.delete(0, tk.END)

        # ファイルリストをクリア
        self.file_list.clear()

        if not self.draft_folder.exists():
            return

        # txtファイルを取得してソート
        txt_files = sorted([f for f in self.draft_folder.glob("*.txt")])

        for file_path in txt_files:
            try:
                # ファイル内容を読み込み
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # ファイル情報をリストに追加
                file_info = {
                    'path': file_path,
                    'name': file_path.name,
                    'content': content
                }
                self.file_list.append(file_info)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                # エラーファイルも表示
                file_info = {
                    'path': file_path,
                    'name': file_path.name,
                    'content': f"[読み込みエラー: {str(e)}]"
                }
                self.file_list.append(file_info)

        # 元の順序を保存（リセット用）
        self.original_file_order = self.file_list.copy()

        # Listboxをプレビュー付きで更新
        self.update_listbox_display()


    def select_all(self):
        """全ファイルを選択"""
        self.draft_listbox.select_set(0, tk.END)

    def deselect_all(self):
        """全選択を解除"""
        self.draft_listbox.selection_clear(0, tk.END)

    def get_selected_files(self):
        """選択されたファイルのパスリストを取得"""
        selected_files = []
        for index in self.draft_listbox.curselection():
            if index < len(self.file_list):
                selected_files.append(self.file_list[index]['path'])
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

    def move_up(self):
        """選択されたファイルを上に移動"""
        selection = self.draft_listbox.curselection()
        if not selection:
            return

        # 最初の選択アイテムのみ処理
        index = selection[0]
        if index <= 0:
            return  # 既に一番上

        # file_list内で順序を入れ替え
        self.file_list[index], self.file_list[index - 1] = self.file_list[index - 1], self.file_list[index]

        # Listboxを更新
        self.update_listbox_display()

        # 選択を新しい位置に維持
        self.draft_listbox.selection_set(index - 1)
        self.draft_listbox.see(index - 1)

    def move_down(self):
        """選択されたファイルを下に移動"""
        selection = self.draft_listbox.curselection()
        if not selection:
            return

        # 最初の選択アイテムのみ処理
        index = selection[0]
        if index >= len(self.file_list) - 1:
            return  # 既に一番下

        # file_list内で順序を入れ替え
        self.file_list[index], self.file_list[index + 1] = self.file_list[index + 1], self.file_list[index]

        # Listboxを更新
        self.update_listbox_display()

        # 選択を新しい位置に維持
        self.draft_listbox.selection_set(index + 1)
        self.draft_listbox.see(index + 1)

    def reset_order(self):
        """ファイル順序を元に戻す（ファイル名昇順）"""
        if not self.original_file_order:
            return

        # 元の順序を復元
        self.file_list = self.original_file_order.copy()

        # Listboxを更新
        self.update_listbox_display()

        messagebox.showinfo("完了", "ファイル順序をリセットしました。")

    def update_listbox_display(self):
        """現在のfile_list順序でListboxを更新（プレビュー付き）"""
        self.draft_listbox.delete(0, tk.END)
        for file_info in self.file_list:
            # プレビューテキストを生成
            content = file_info['content']
            if content.startswith('[読み込みエラー:'):
                # エラーファイルの場合
                display_text = f"{file_info['name']}: {content}"
            else:
                # 通常ファイルの場合
                preview = content[:self.preview_length]
                if len(content) > self.preview_length:
                    preview += "..."
                # 改行をスペースに変換
                preview = preview.replace('\n', ' ').replace('\r', ' ')
                display_text = f"{file_info['name']}: {preview}"

            self.draft_listbox.insert(tk.END, display_text)

    def edit_file(self):
        """選択されたファイルを編集"""
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "編集するファイルを選択してください。")
            return

        if len(selected_files) > 1:
            messagebox.showwarning("警告", "編集は1つのファイルのみ選択してください。")
            return

        file_path = selected_files[0]
        EditWindow(self.root, file_path, self.refresh_file_list)

    def load_last_number(self):
        """last_number.jsonを読み込み"""
        try:
            if self.last_number_file.exists():
                with open(self.last_number_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('date', ''), data.get('last_number', 0)
            else:
                return '', 0
        except Exception as e:
            print(f"last_number.json読み込みエラー: {e}")
            return '', 0

    def save_last_number(self, date, last_number):
        """last_number.jsonを保存"""
        try:
            data = {
                'date': date,
                'last_number': last_number
            }
            with open(self.last_number_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"last_number.json保存エラー: {e}")

    def get_next_numbers(self, count):
        """必要な連番リストを取得"""
        today = datetime.now().strftime('%Y%m%d')
        saved_date, last_number = self.load_last_number()

        # 日付が変わった場合は001から開始
        if saved_date != today:
            start_number = 1
        else:
            start_number = last_number + 1

        # 999を超えるかチェック
        if start_number + count - 1 > 999:
            raise ValueError(f"連番が999を超えます。開始番号: {start_number}, 必要数: {count}")

        return today, list(range(start_number, start_number + count))

    def generate_new_filename(self, original_name, date, number):
        """新しいファイル名を生成"""
        # 拡張子を除去
        base_name = original_name.replace('.txt', '')
        # YYYYMMDDNNN_元ファイル名.txt の形式
        return f"{date}{number:03d}_{base_name}.txt"

    def move_to_sns(self):
        """選択されたファイルを表示順序でSNSフォルダへ移動"""
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "SNSへ移動するファイルを選択してください。")
            return

        # 選択されたファイルを現在の表示順序で整理
        selected_files_ordered = []
        for file_info in self.file_list:
            if file_info['path'] in selected_files:
                selected_files_ordered.append(file_info)

        try:
            # 連番を取得
            date, numbers = self.get_next_numbers(len(selected_files_ordered))

            # リネーム後のファイル名プレビューを作成
            rename_preview = []
            for i, file_info in enumerate(selected_files_ordered):
                new_filename = self.generate_new_filename(file_info['name'], date, numbers[i])
                rename_preview.append(f"{file_info['name']} → {new_filename}")

            # 確認ダイアログにプレビューを表示
            preview_text = "\n".join(rename_preview[:10])  # 最初の10個まで表示
            if len(rename_preview) > 10:
                preview_text += f"\n... 他{len(rename_preview) - 10}個"

            confirmation_msg = f"選択されたファイルを以下の順序でSNSフォルダに移動しますか？\n\n{preview_text}"

            if not messagebox.askyesno("確認", confirmation_msg):
                return

        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        except Exception as e:
            messagebox.showerror("エラー", f"連番生成エラー: {str(e)}")
            return

        # ファイル移動処理
        try:
            moved_count = 0
            temp_files = []  # 一時ファイル名を記録

            # Step 1: 一時ファイル名でリネーム（衝突防止）
            for i, file_info in enumerate(selected_files_ordered):
                file_path = file_info['path']
                temp_filename = f"temp_{i}_{file_path.name}"
                temp_path = self.sns_folder / temp_filename

                # 一時ファイル名でSNSフォルダに移動
                shutil.move(str(file_path), str(temp_path))
                temp_files.append((temp_path, self.generate_new_filename(file_path.name, date, numbers[i])))

            # Step 2: 最終ファイル名にリネーム
            for temp_path, final_filename in temp_files:
                final_path = self.sns_folder / final_filename

                # 最終名にリネーム
                shutil.move(str(temp_path), str(final_path))
                moved_count += 1

            # last_number.jsonを更新
            final_number = numbers[-1]  # 最後の番号
            self.save_last_number(date, final_number)

            # UI更新と完了メッセージ
            self.refresh_file_list()

            if len(numbers) == 1:
                range_text = f"{date}{numbers[0]:03d}"
            else:
                range_text = f"{date}{numbers[0]:03d}～{numbers[-1]:03d}"

            messagebox.showinfo("完了", f"{moved_count}件を {range_text} の番号でSNSフォルダに移動しました。")

        except Exception as e:
            # エラー時のクリーンアップ（一時ファイルが残っている場合）
            for i, (temp_path, _) in enumerate(temp_files):
                try:
                    if temp_path.exists():
                        # 元のdraftフォルダに戻す
                        original_name = temp_path.name.replace(f"temp_{i}_", "")
                        shutil.move(str(temp_path), str(self.draft_folder / original_name))
                except:
                    pass  # クリーンアップ失敗は無視

            messagebox.showerror("エラー", f"ファイル移動中にエラーが発生しました:\n{str(e)}")
            self.refresh_file_list()


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