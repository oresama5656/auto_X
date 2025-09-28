#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Draft File Mixer - draftフォルダのファイルをブログ投稿分散配置でミックス
ブログ投稿を10回に1回の割合で配置
"""

import os
import shutil
import re
from pathlib import Path

def analyze_file_content(file_path):
    """ファイル内容を分析してブログ投稿かどうか判定"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # ブログリンクを含む投稿かチェック
        if 'www.coommu.com' in content:
            return 'blog'

        return 'regular'
    except:
        return 'regular'

def categorize_files(draft_dir):
    """ファイルをカテゴリ別に分類"""
    files = [f for f in os.listdir(draft_dir) if f.startswith('mix_') and f.endswith('.txt')]

    blog_posts = []
    short_tips = []
    expert_posts = []
    regular_posts = []

    for file in files:
        file_path = os.path.join(draft_dir, file)

        # ファイル名パターンでの分類
        if file.endswith('-sns.txt'):
            # さらに内容チェック
            if analyze_file_content(file_path) == 'blog':
                blog_posts.append(file)
            else:
                expert_posts.append(file)
        elif re.search(r'-0[0-9]\.txt$', file):
            short_tips.append(file)
        else:
            regular_posts.append(file)

    return blog_posts, short_tips, expert_posts, regular_posts

def create_optimal_mix(blog_posts, short_tips, expert_posts, regular_posts):
    """10回に1回ブログ投稿の最適ミックス作成"""

    # 通常投稿を結合
    regular_content = short_tips + expert_posts + regular_posts

    total_files = len(blog_posts) + len(regular_content)
    mixed_list = [''] * total_files

    # ブログ投稿を10, 20, 30... の位置に配置
    blog_positions = []
    for i in range(10, total_files + 1, 10):
        if i <= total_files:
            blog_positions.append(i - 1)  # 0-indexed

    # ブログ投稿を配置
    blog_index = 0
    for pos in blog_positions:
        if blog_index < len(blog_posts) and pos < total_files:
            mixed_list[pos] = blog_posts[blog_index]
            blog_index += 1

    # 残りのブログ投稿を末尾に追加
    while blog_index < len(blog_posts):
        for i in range(total_files):
            if mixed_list[i] == '':
                mixed_list[i] = blog_posts[blog_index]
                blog_index += 1
                break

    # 通常投稿を空いている位置に配置
    regular_index = 0
    for i in range(total_files):
        if mixed_list[i] == '' and regular_index < len(regular_content):
            mixed_list[i] = regular_content[regular_index]
            regular_index += 1

    return [f for f in mixed_list if f != '']

def backup_and_rename_files(draft_dir, mixed_list):
    """バックアップ作成後にファイルをリネーム"""

    # 既存のmix_ファイルを一時的にリネーム
    temp_files = []
    print("Step 1完了: {}のファイルを一時リネーム".format(len(mixed_list)))

    for i, filename in enumerate(mixed_list, 1):
        old_path = os.path.join(draft_dir, filename)
        temp_name = f"temp_{i:03d}_{filename}"
        temp_path = os.path.join(draft_dir, temp_name)

        if os.path.exists(old_path):
            shutil.move(old_path, temp_path)
            temp_files.append((temp_path, f"draft_mix_{i:03d}_{filename.replace('mix_', '').replace('temp_', '')}"))

    # 最終的なリネーム
    print("Step 2完了: 全ファイルをdraft_mix_XXX_形式にリネーム完了")
    for temp_path, final_name in temp_files:
        final_path = os.path.join(draft_dir, final_name)
        shutil.move(temp_path, final_path)

    return len(temp_files)

def main():
    draft_dir = r"C:\Users\PHARMY\Desktop\TEST\auto_X\sns\draft"

    if not os.path.exists(draft_dir):
        print(f"エラー: {draft_dir} が見つかりません")
        return

    print(f"draftフォルダ: {draft_dir}")

    # ファイル分類
    print("draftファイルを分類中...")
    blog_posts, short_tips, expert_posts, regular_posts = categorize_files(draft_dir)

    total = len(blog_posts) + len(short_tips) + len(expert_posts) + len(regular_posts)
    print(f"合計: {total}件")
    print()

    # 最適ミックス作成
    print("ブログ投稿10回に1回配置の最適ミックス順序を作成中...")
    mixed_list = create_optimal_mix(blog_posts, short_tips, expert_posts, regular_posts)

    print("ファイル内訳分析:")
    print(f"  ブログ紹介投稿: {len(blog_posts)}件")
    print(f"  短文Tips: {len(short_tips)}件")
    print(f"  専門投稿: {len(expert_posts)}件")
    print(f"  通常投稿合計: {len(short_tips) + len(expert_posts) + len(regular_posts)}件")
    print(f"ミックス順序を作成しました({len(mixed_list)}件)")
    print()

    # ファイルリネーム
    print("ファイルをdraft_mix_XXX_形式でリネーム中...")
    processed_count = backup_and_rename_files(draft_dir, mixed_list)

    print(f"開始: {total}件のdraftファイルをブログ最適分散でリネーム")
    print(f"処理済み: {processed_count}件")

    # ブログ投稿配置位置表示
    blog_positions = []
    for i, filename in enumerate(mixed_list, 1):
        if any(blog in filename for blog in blog_posts):
            blog_positions.append(i)

    print(f"ブログ投稿配置位置: {blog_positions[:10]}...")
    print()
    print("✅ draftファイルミックス完了!")

if __name__ == "__main__":
    main()