# -*- coding: utf-8 -*-
"""
GUI ユーティリティ関数

JSON読み書き、文字列処理など共通機能
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    設定ファイル(sns.json)を読み込み
    
    Args:
        config_path: 設定ファイルのパス（Noneの場合はデフォルト）
    
    Returns:
        設定辞書
        
    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合
        json.JSONDecodeError: JSONの解析に失敗した場合
    """
    if config_path is None:
        config_path = Path.cwd() / 'configs' / 'sns.json'
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config: Dict[str, Any], config_path: str = None) -> None:
    """
    設定ファイル(sns.json)を保存
    
    Args:
        config: 設定辞書
        config_path: 設定ファイルのパス（Noneの場合はデフォルト）
        
    Raises:
        OSError: ファイル書き込みに失敗した場合
    """
    if config_path is None:
        config_path = Path.cwd() / 'configs' / 'sns.json'
    else:
        config_path = Path(config_path)
    
    # ディレクトリが存在しない場合は作成
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # UTF-8で整形して保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_sns_files() -> List[str]:
    """
    sns/ディレクトリから投稿待ちファイルを取得

    Returns:
        ファイル名のリスト（昇順ソート済み）
    """
    sns_dir = Path.cwd() / 'sns'

    if not sns_dir.exists():
        return []

    # *.txt パターンのファイルを検索（CLI と同じ形式）
    files = []
    for file_path in sns_dir.glob('*.txt'):
        # README.txt は除外
        if file_path.name == 'README.txt':
            continue
        # postedディレクトリ内は除外
        if 'posted' not in str(file_path):
            files.append(file_path.name)

    # ファイル名でソート（投稿順序と一致）
    return sorted(files)


def parse_post_time(input_str: str) -> str:
    """
    postTime入力文字列をJSON用に変換
    
    Args:
        input_str: ユーザー入力 ("auto" または "09:30")
        
    Returns:
        JSON用文字列 ("auto" または "09:30")
    """
    return input_str.strip()


def parse_fixed_times(input_str: str) -> List[str]:
    """
    fixedTimes入力文字列を配列に変換
    
    Args:
        input_str: カンマ区切り文字列 ("09:00,12:00,15:00")
        
    Returns:
        時刻配列 ["09:00", "12:00", "15:00"]
    """
    if not input_str.strip():
        return []
    
    return [time.strip() for time in input_str.split(',') if time.strip()]


def format_fixed_times(times_list: List[str]) -> str:
    """
    fixedTimes配列をGUI表示用文字列に変換
    
    Args:
        times_list: 時刻配列 ["09:00", "12:00", "15:00"]
        
    Returns:
        カンマ区切り文字列 "09:00,12:00,15:00"
    """
    return ','.join(times_list)


def validate_time_format(time_str: str) -> bool:
    """
    時刻文字列のフォーマット検証

    Args:
        time_str: 時刻文字列 ("HH:MM")

    Returns:
        フォーマットが正しい場合True
    """
    if time_str == "auto":
        return True

    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            return False

        hour, minute = int(parts[0]), int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, IndexError):
        return False


def read_workflow_times() -> str:
    """
    GitHub Actionsワークフローファイルから現在の投稿時刻を読み取り

    Returns:
        JST時刻のカンマ区切り文字列 ("10:00,11:00,12:00,13:00,16:00,18:00,19:00")
        読み取りに失敗した場合は空文字列
    """
    try:
        workflow_path = Path.cwd() / '.github' / 'workflows' / 'sns.yml'
        if not workflow_path.exists():
            return ""

        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # cron式を抽出 (例: "0 1,2,3,4,7,9,10 * * *")
        cron_match = re.search(r'cron:\s*[\'"]([^\'\"]+)[\'"]', content)
        if not cron_match:
            return ""

        cron_expr = cron_match.group(1).strip()

        # cron式をパース (分 時 日 月 曜日)
        parts = cron_expr.split()
        if len(parts) < 2:
            return ""

        minutes_str = parts[0]  # 例: "0" または "15,45"
        hours_str = parts[1]    # 例: "1,2,3,4,7,9,10"

        # 分を解析
        if minutes_str == '*':
            minutes = [0]  # デフォルトは毎時0分
        else:
            try:
                minutes = [int(m.strip()) for m in minutes_str.split(',') if m.strip()]
                # 分の範囲チェック
                for m in minutes:
                    if not (0 <= m <= 59):
                        return ""
            except ValueError:
                return ""

        # 時を解析
        if hours_str == '*':
            return ""  # 毎時実行は想定外

        try:
            utc_hours = [int(h.strip()) for h in hours_str.split(',') if h.strip()]
            # 時の範囲チェック
            for h in utc_hours:
                if not (0 <= h <= 23):
                    return ""
        except ValueError:
            return ""

        # UTC→JST変換して時刻リストを生成
        jst_times = []
        for utc_hour in utc_hours:
            for minute in minutes:
                # UTC→JST (+9時間)
                jst_hour = (utc_hour + 9) % 24
                jst_times.append(f"{jst_hour:02d}:{minute:02d}")

        # 時刻順にソート
        jst_times.sort()

        return ','.join(jst_times)

    except Exception:
        # エラーが発生した場合は空文字列を返す
        return ""