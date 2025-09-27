#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Draft File Mixer - SNS投稿ファイルをバランス良くミックス
"""

import os
import random
from pathlib import Path
import shutil

def categorize_files(draft_folder):
    """ファイルをカテゴリ別に分類"""
    files = list(Path(draft_folder).glob("*.txt"))

    categories = {
        'expert': [],      # 専門記事系 (-sns.txt)
        'experience': [],  # 体験談系 (-04.txt)
        'other': []        # その他
    }

    for file in files:
        if file.name.endswith('-sns.txt'):
            categories['expert'].append(file)
        elif file.name.endswith('-04.txt'):
            categories['experience'].append(file)
        else:
            categories['other'].append(file)

    # 各カテゴリ内でランダム化
    for category in categories.values():
        random.shuffle(category)

    return categories

def create_balanced_mix(categories):
    """バランス良いミックス順序を作成"""
    mixed_order = []

    # 各カテゴリの最大数を取得
    max_expert = len(categories['expert'])
    max_experience = len(categories['experience'])
    max_other = len(categories['other'])
    max_length = max(max_expert, max_experience, max_other)

    # 3種ローテーションでバランス良く配置
    for i in range(max_length):
        # 専門記事 → 体験談 → その他 の順序で配置
        if i < max_expert:
            mixed_order.append(categories['expert'][i])
        if i < max_experience:
            mixed_order.append(categories['experience'][i])
        if i < max_other:
            mixed_order.append(categories['other'][i])

    return mixed_order

def rename_files_with_mix_prefix(mixed_order, draft_folder):
    """ファイルをmix_XXX_形式でリネーム"""
    temp_files = []  # 一時ファイル名を記録

    print(f"開始: {len(mixed_order)}個のファイルをミックス順序でリネーム")

    try:
        # Step 1: 一時ファイル名にリネーム（衝突防止）
        for i, file_path in enumerate(mixed_order, 1):
            temp_name = f"temp_{i:03d}_{file_path.name}"
            temp_path = draft_folder / temp_name

            # 一時ファイル名にリネーム
            shutil.move(str(file_path), str(temp_path))
            temp_files.append((temp_path, f"mix_{i:03d}_{file_path.name}"))

        print(f"Step 1完了: {len(temp_files)}個のファイルを一時リネーム")

        # Step 2: 最終ファイル名にリネーム
        for temp_path, final_name in temp_files:
            final_path = draft_folder / final_name
            shutil.move(str(temp_path), str(final_path))

        print(f"Step 2完了: 全ファイルをmix_XXX_形式にリネーム完了")

        return True

    except Exception as e:
        print(f"エラー発生: {e}")

        # エラー時のクリーンアップ
        print("エラー時のクリーンアップを実行中...")
        for i, (temp_path, _) in enumerate(temp_files):
            try:
                if temp_path.exists():
                    # 元のファイル名に戻す
                    original_name = temp_path.name.replace(f"temp_{i+1:03d}_", "")
                    original_path = draft_folder / original_name
                    shutil.move(str(temp_path), str(original_path))
            except:
                pass  # クリーンアップ失敗は無視

        return False

def main():
    """メイン処理"""
    # draft フォルダのパス
    script_dir = Path(__file__).parent
    draft_folder = script_dir.parent / "sns" / "draft"

    if not draft_folder.exists():
        print(f"エラー: draftフォルダが見つかりません: {draft_folder}")
        return

    print(f"draftフォルダ: {draft_folder}")

    # ファイルを分類
    print("ファイルを分類中...")
    categories = categorize_files(draft_folder)

    print(f"分類結果:")
    print(f"  専門記事系: {len(categories['expert'])}件")
    print(f"  体験談系: {len(categories['experience'])}件")
    print(f"  その他: {len(categories['other'])}件")
    print(f"  合計: {sum(len(cat) for cat in categories.values())}件")

    if sum(len(cat) for cat in categories.values()) == 0:
        print("処理対象のファイルがありません。")
        return

    # バランス良いミックス順序を作成
    print("\nバランス良いミックス順序を作成中...")
    mixed_order = create_balanced_mix(categories)

    print(f"ミックス順序を作成しました（{len(mixed_order)}件）")

    # 自動実行（確認スキップ）
    print("\nファイルをmix_XXX_形式でリネームします...")

    # ファイルをリネーム
    success = rename_files_with_mix_prefix(mixed_order, draft_folder)

    if success:
        print("\n✅ ファイルミックス完了！")
        print("投稿順序がバランス良く調整されました。")
        print(f"専門記事 → 体験談 → その他 の順序で配置済み")
    else:
        print("\n❌ ファイルミックス中にエラーが発生しました。")

if __name__ == "__main__":
    main()