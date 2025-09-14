# -*- coding: utf-8 -*-
"""
Git操作管理機能

設定変更をGitHubに反映するためのGit操作
"""

import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional


class GitManager:
    """Git操作管理クラス"""
    
    def __init__(self, work_dir: Optional[str] = None):
        """
        Git管理オブジェクトを初期化
        
        Args:
            work_dir: 作業ディレクトリ（Noneの場合は現在のディレクトリ）
        """
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        
    def check_git_status(self) -> bool:
        """
        Gitリポジトリの状態確認
        
        Returns:
            Git管理下の場合True
        """
        try:
            result = subprocess.run(
                ['git', 'status'],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_git_status(self) -> dict:
        """
        Git状態の詳細取得
        
        Returns:
            Git状態情報の辞書
        """
        try:
            # git status --porcelain
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.returncode != 0:
                return {'error': 'Git status取得失敗'}
            
            # 変更ファイルを解析
            changes = []
            for line in status_result.stdout.strip().split('\n'):
                if line.strip():
                    status_code = line[:2]
                    file_path = line[3:]
                    changes.append({'status': status_code, 'file': file_path})
            
            # ブランチ情報取得
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else 'unknown'
            
            return {
                'has_changes': len(changes) > 0,
                'changes': changes,
                'current_branch': current_branch
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def commit_and_push(
        self, 
        file_paths: list, 
        commit_message: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        completion_callback: Optional[Callable[[bool, str], None]] = None
    ):
        """
        ファイルをコミット・プッシュ（バックグラウンド実行）
        
        Args:
            file_paths: コミット対象ファイルのパス一覧
            commit_message: コミットメッセージ
            progress_callback: 進行状況コールバック
            completion_callback: 完了コールバック(成功フラグ, メッセージ)
        """
        def execute():
            try:
                if progress_callback:
                    progress_callback("Git操作を開始...")
                
                # git add
                if progress_callback:
                    progress_callback("ファイルをステージング中...")
                    
                add_cmd = ['git', 'add'] + file_paths
                add_result = subprocess.run(
                    add_cmd,
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if add_result.returncode != 0:
                    raise Exception(f"git add失敗: {add_result.stderr}")
                
                # git commit
                if progress_callback:
                    progress_callback("コミット中...")
                    
                commit_result = subprocess.run(
                    ['git', 'commit', '-m', commit_message],
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if commit_result.returncode != 0:
                    raise Exception(f"git commit失敗: {commit_result.stderr}")
                
                # git push
                if progress_callback:
                    progress_callback("GitHubにプッシュ中...")
                    
                push_result = subprocess.run(
                    ['git', 'push'],
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if push_result.returncode != 0:
                    raise Exception(f"git push失敗: {push_result.stderr}")
                
                if completion_callback:
                    completion_callback(True, "GitHubへの反映が完了しました")
                    
            except subprocess.TimeoutExpired:
                if completion_callback:
                    completion_callback(False, "Git操作がタイムアウトしました")
            except Exception as e:
                if completion_callback:
                    completion_callback(False, f"Git操作エラー: {str(e)}")
        
        # バックグラウンドで実行
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
    
    def generate_commit_message(self, file_paths: list) -> str:
        """
        変更内容に基づいてコミットメッセージを自動生成
        
        Args:
            file_paths: 変更されたファイルのパス
            
        Returns:
            生成されたコミットメッセージ
        """
        config_files = [p for p in file_paths if 'sns.json' in p]
        workflow_files = [p for p in file_paths if 'sns.yml' in p or 'workflow' in p]
        
        changes = []
        if config_files:
            changes.append("投稿設定更新")
        if workflow_files:
            changes.append("GitHub Actions最適化")
        
        if not changes:
            changes.append("設定ファイル更新")
        
        message = f"feat: {', '.join(changes)}\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        return message
    
    def pull_from_remote(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
        completion_callback: Optional[Callable[[bool, str], None]] = None
    ):
        """
        リモートからpullを実行（バックグラウンド実行）

        Args:
            progress_callback: 進行状況コールバック
            completion_callback: 完了コールバック(成功フラグ, メッセージ)
        """
        def execute():
            try:
                if progress_callback:
                    progress_callback("最新情報を取得中...")

                # git pull
                pull_result = subprocess.run(
                    ['git', 'pull'],
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if pull_result.returncode != 0:
                    # マージ競合の可能性をチェック
                    if "CONFLICT" in pull_result.stdout or "CONFLICT" in pull_result.stderr:
                        raise Exception(f"マージ競合が発生しました。手動で解決してください。")
                    else:
                        raise Exception(f"git pull失敗: {pull_result.stderr}")

                # 結果解析
                output = pull_result.stdout.strip()
                if "Already up to date" in output:
                    message = "既に最新状態です"
                elif "Fast-forward" in output or "Merge made" in output:
                    message = "最新情報を取得しました"
                else:
                    message = "同期が完了しました"

                if completion_callback:
                    completion_callback(True, message)

            except subprocess.TimeoutExpired:
                if completion_callback:
                    completion_callback(False, "Git pullがタイムアウトしました")
            except Exception as e:
                if completion_callback:
                    completion_callback(False, f"Git pullエラー: {str(e)}")

        # バックグラウンドで実行
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()

    def check_remote_changes(self) -> dict:
        """
        リモートの変更をチェック

        Returns:
            {
                'has_changes': bool,  # リモートに変更あり
                'behind_count': int,  # ローカルが遅れているコミット数
                'ahead_count': int,   # ローカルが進んでいるコミット数
                'error': str         # エラーメッセージ
            }
        """
        try:
            # git fetch
            fetch_result = subprocess.run(
                ['git', 'fetch'],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if fetch_result.returncode != 0:
                return {'error': f'git fetch失敗: {fetch_result.stderr}'}

            # リモートとの差分をチェック
            status_result = subprocess.run(
                ['git', 'status', '-b', '--porcelain'],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=10
            )

            if status_result.returncode != 0:
                return {'error': 'git status取得失敗'}

            # 第一行からブランチ情報を解析
            lines = status_result.stdout.strip().split('\n')
            if not lines:
                return {'has_changes': False, 'behind_count': 0, 'ahead_count': 0}

            branch_line = lines[0]
            behind_count = 0
            ahead_count = 0

            # [behind N] または [ahead N] を検索
            import re
            behind_match = re.search(r'\[behind (\d+)\]', branch_line)
            ahead_match = re.search(r'\[ahead (\d+)\]', branch_line)

            if behind_match:
                behind_count = int(behind_match.group(1))
            if ahead_match:
                ahead_count = int(ahead_match.group(1))

            return {
                'has_changes': behind_count > 0,
                'behind_count': behind_count,
                'ahead_count': ahead_count
            }

        except subprocess.TimeoutExpired:
            return {'error': 'Git操作がタイムアウトしました'}
        except Exception as e:
            return {'error': str(e)}

    def is_git_available(self) -> bool:
        """
        Gitコマンドが利用可能か確認

        Returns:
            Git利用可能な場合True
        """
        try:
            subprocess.run(
                ['git', '--version'],
                capture_output=True,
                timeout=5
            )
            return True
        except Exception:
            return False