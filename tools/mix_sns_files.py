#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SNS File Mixer - SNS投稿ファイルをブログ紹介リンク付きでバランス良くミックス
ブログ紹介投稿を10回に1回の割合で配置
"""

import os
import random
from pathlib import Path
import shutil

def categorize_sns_files(sns_folder):
    """SNSファイルをカテゴリ別に分類"""
    files = list(Path(sns_folder).glob("*.txt"))

    categories = {
        'blog': [],        # ブログ紹介投稿 (www.coommu.com リンク含有)
        'short_tips': [],  # 短文Tips (-0X.txt)
        'professional': [] # 専門投稿 (その他)
    }

    for file in files:
        try:
            # ファイル内容を読み込んでリンクチェック
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'www.coommu.com' in content:
                categories['blog'].append(file)
            elif file.name.endswith(('-05.txt', '-06.txt', '-07.txt', '-02.txt')):
                categories['short_tips'].append(file)
            else:
                categories['professional'].append(file)

        except Exception as e:
            print(f"ファイル読み込みエラー: {file.name} - {e}")
            # エラーファイルは専門投稿として分類
            categories['professional'].append(file)

    # 各カテゴリ内でランダム化
    for category in categories.values():
        random.shuffle(category)

    return categories

def create_blog_optimized_mix(categories):
    """ブログ紹介投稿を10回に1回配置する最適ミックス順序を作成"""
    mixed_order = []

    blog_posts = categories['blog']
    short_tips = categories['short_tips']
    professional = categories['professional']

    # 通常投稿（短文Tips + 専門投稿）をミックス
    regular_posts = short_tips + professional
    random.shuffle(regular_posts)

    print(f"ファイル分類結果:")
    print(f"  ブログ紹介投稿: {len(blog_posts)}件")
    print(f"  短文Tips: {len(short_tips)}件")
    print(f"  専門投稿: {len(professional)}件")
    print(f"  通常投稿合計: {len(regular_posts)}件")

    # 10回に1回の割合でブログ投稿を配置
    blog_index = 0
    regular_index = 0

    position = 1
    while regular_index < len(regular_posts) or blog_index < len(blog_posts):
        # 10の倍数位置にブログ投稿を配置
        if position % 10 == 0 and blog_index < len(blog_posts):
            mixed_order.append(blog_posts[blog_index])
            blog_index += 1
        else:
            # 通常投稿を配置
            if regular_index < len(regular_posts):
                mixed_order.append(regular_posts[regular_index])
                regular_index += 1

        position += 1

    # 残ったブログ投稿があれば最後に追加
    while blog_index < len(blog_posts):
        mixed_order.append(blog_posts[blog_index])
        blog_index += 1

    return mixed_order

def rename_sns_files_with_mix_prefix(mixed_order, sns_folder):
    """SNSファイルをsns_mix_XXX_形式でリネーム"""
    temp_files = []  # 一時ファイル名を記録

    print(f"開始: {len(mixed_order)}個のSNSファイルをブログ最適化順序でリネーム")

    try:
        # Step 1: 一時ファイル名にリネーム（衝突防止）
        for i, file_path in enumerate(mixed_order, 1):
            temp_name = f"sns_temp_{i:03d}_{file_path.name}"
            temp_path = sns_folder / temp_name

            # 一時ファイル名にリネーム
            shutil.move(str(file_path), str(temp_path))
            temp_files.append((temp_path, f"sns_mix_{i:03d}_{file_path.name}"))

        print(f"Step 1完了: {len(temp_files)}個のファイルを一時リネーム")

        # Step 2: 最終ファイル名にリネーム
        blog_positions = []
        for i, (temp_path, final_name) in enumerate(temp_files, 1):
            final_path = sns_folder / final_name
            shutil.move(str(temp_path), str(final_path))

            # ブログ投稿の位置を記録
            temp_content_check = final_name
            if i % 10 == 0:  # 10の倍数位置をチェック
                blog_positions.append(i)

        print(f"Step 2完了: 全ファイルをsns_mix_XXX_形式にリネーム完了")
        print(f"ブログ投稿配置位置: {blog_positions[:10]}..." if len(blog_positions) > 10 else f"ブログ投稿配置位置: {blog_positions}")

        return True

    except Exception as e:
        print(f"エラー発生: {e}")

        # エラー時のクリーンアップ
        print("エラー時のクリーンアップを実行中...")
        for i, (temp_path, _) in enumerate(temp_files):
            try:
                if temp_path.exists():
                    # 元のファイル名に戻す
                    original_name = temp_path.name.replace(f"sns_temp_{i+1:03d}_", "")
                    original_path = sns_folder / original_name
                    shutil.move(str(temp_path), str(original_path))
            except:
                pass  # クリーンアップ失敗は無視

        return False

def main():
    """メイン処理"""
    # sns フォルダのパス
    script_dir = Path(__file__).parent
    sns_folder = script_dir.parent / "sns"

    if not sns_folder.exists():
        print(f"エラー: snsフォルダが見つかりません: {sns_folder}")
        return

    print(f"snsフォルダ: {sns_folder}")

    # ファイルを分類
    print("SNSファイルを分類中...")
    categories = categorize_sns_files(sns_folder)

    total_files = sum(len(cat) for cat in categories.values())
    print(f"合計: {total_files}件")

    if total_files == 0:
        print("処理対象のファイルがありません。")
        return

    # ブログ最適化ミックス順序を作成
    print("\nブログ投稿10回に1回配置の最適ミックス順序を作成中...")
    mixed_order = create_blog_optimized_mix(categories)

    print(f"ミックス順序を作成しました（{len(mixed_order)}件）")

    # 自動実行
    print("\nファイルをsns_mix_XXX_形式でリネームします...")

    # ファイルをリネーム
    success = rename_sns_files_with_mix_prefix(mixed_order, sns_folder)

    if success:
        print("\n✅ SNSファイルミックス完了！")
        print("ブログ紹介投稿が10回に1回の最適な頻度で配置されました。")
        print("エンゲージメントとリンククリック率の向上が期待できます！")
    else:
        print("\n❌ SNSファイルミックス中にエラーが発生しました。")

if __name__ == "__main__":
    main()