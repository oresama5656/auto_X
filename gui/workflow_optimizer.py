# -*- coding: utf-8 -*-
"""
GitHub Actions ワークフロー最適化機能

固定時刻設定に基づいてGitHub Actionsの実行頻度を最適化
"""

import json
import re
from pathlib import Path
from typing import List


def optimize_cron_for_times(times: List[str]) -> str:
    """
    投稿時刻リストから最適化されたcron式を生成（JST→UTC変換）

    Args:
        times: JST投稿時刻のリスト ["09:00", "12:00", "18:00"]

    Returns:
        UTC基準のcron式 "0 0,3,9 * * *"
    """
    if not times:
        # デフォルトは毎時実行
        return '0 * * * *'

    # JST時刻をUTC時刻に変換
    utc_hours = []
    for time_str in times:
        try:
            jst_hour = int(time_str.split(':')[0])
            # JST → UTC 変換（JST - 9時間）
            utc_hour = (jst_hour - 9) % 24
            utc_hours.append(utc_hour)
        except (ValueError, IndexError):
            continue

    if not utc_hours:
        return '0 * * * *'

    # 重複を除去してソート
    unique_hours = sorted(set(utc_hours))

    # cron式を生成
    hours_str = ','.join(map(str, unique_hours))
    return f'0 {hours_str} * * *'


def update_workflow_cron(times: List[str], workflow_path: str = None) -> bool:
    """
    GitHub Actionsワークフローファイルのcron設定を更新
    
    Args:
        times: 投稿時刻のリスト
        workflow_path: ワークフローファイルのパス
        
    Returns:
        更新成功時True
    """
    try:
        if workflow_path is None:
            workflow_path = Path.cwd() / '.github' / 'workflows' / 'sns.yml'
        else:
            workflow_path = Path(workflow_path)
        
        if not workflow_path.exists():
            raise FileNotFoundError(f"ワークフローファイルが見つかりません: {workflow_path}")
        
        # 最適化されたcron式を生成
        new_cron = optimize_cron_for_times(times)
        
        # ファイルを読み込み
        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # cron設定を置き換え
        # パターン: - cron: '0 * * * *' または - cron: '0 9,12,18 * * *'
        cron_pattern = r"(\s*-\s*cron:\s*['\"])(.*?)(['\"])"
        
        def replace_cron(match):
            prefix = match.group(1)
            suffix = match.group(3)
            return f"{prefix}{new_cron}{suffix}"
        
        new_content = re.sub(cron_pattern, replace_cron, content)
        
        if new_content == content:
            # 変更がない場合
            return True
        
        # ファイルに書き戻し
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"ワークフロー更新エラー: {e}")
        return False


def get_execution_frequency_info(times: List[str]) -> dict:
    """
    実行頻度情報を取得
    
    Args:
        times: 投稿時刻のリスト
        
    Returns:
        実行頻度情報の辞書
    """
    if not times:
        return {
            'executions_per_day': 24,
            'cron_expression': '0 * * * *',
            'description': '毎時実行'
        }
    
    unique_hours = len(set(int(time.split(':')[0]) for time in times))
    cron_expr = optimize_cron_for_times(times)
    
    return {
        'executions_per_day': unique_hours,
        'cron_expression': cron_expr,
        'description': f'1日{unique_hours}回実行',
        'savings_percent': round((24 - unique_hours) / 24 * 100, 1)
    }


def format_times_for_display(times: List[str]) -> str:
    """
    時刻リストを表示用にフォーマット
    
    Args:
        times: 投稿時刻のリスト
        
    Returns:
        フォーマット済み文字列
    """
    if not times:
        return "設定なし"
    
    return ', '.join(times)


def validate_workflow_file(workflow_path: str = None) -> bool:
    """
    ワークフローファイルの存在確認
    
    Args:
        workflow_path: ワークフローファイルのパス
        
    Returns:
        ファイルが存在し、cron設定が見つかる場合True
    """
    try:
        if workflow_path is None:
            workflow_path = Path.cwd() / '.github' / 'workflows' / 'sns.yml'
        else:
            workflow_path = Path(workflow_path)
        
        if not workflow_path.exists():
            return False
        
        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # cron設定の存在確認
        cron_pattern = r"\s*-\s*cron:\s*['\"].*?['\"]"
        return bool(re.search(cron_pattern, content))
        
    except Exception:
        return False