# -*- coding: utf-8 -*-
"""
GUI ユーティリティ関数

JSON読み書き、文字列処理など共通機能
"""

import json
import os
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
    
    # *-sns.txt パターンのファイルを検索（posted/は除外）
    files = []
    for file_path in sns_dir.glob('*-sns.txt'):
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