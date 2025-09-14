#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_X GUI - X (Twitter) 自動投稿システムのGUIツール

起動方法:
    python gui.py

要件:
    - Python 3.6+
    - tkinter (標準ライブラリ)
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import tkinter as tk
    from tkinter import messagebox
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"必要なモジュールが見つかりません: {e}")
    print("tkinterが正しくインストールされているか確認してください。")
    sys.exit(1)


def main():
    """GUIアプリケーションのエントリーポイント"""
    try:
        # プロジェクトルートの確認
        if not (project_root / 'configs').exists():
            messagebox.showerror(
                "エラー", 
                f"auto_Xプロジェクトのルートディレクトリで実行してください。\n"
                f"現在のディレクトリ: {project_root}"
            )
            return

        # メインウィンドウを作成・実行
        app = MainWindow()
        app.run()
        
    except Exception as e:
        messagebox.showerror("予期しないエラー", f"アプリケーションの起動に失敗しました:\n{str(e)}")
        print(f"エラー詳細: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()