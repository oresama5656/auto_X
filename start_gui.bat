@echo off
chcp 65001 > nul
title auto_X GUI - X (Twitter) 自動投稿システム

echo ===============================================
echo  auto_X GUI - X (Twitter) 自動投稿システム
echo ===============================================
echo.

REM カレントディレクトリをバッチファイルの場所に変更
cd /d "%~dp0"

echo 起動中...
echo.

REM Pythonの存在確認
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonが見つかりません。
    echo Python 3.6以上をインストールしてください。
    echo.
    pause
    exit /b 1
)

REM GUI起動
python gui.py

REM 終了処理
if errorlevel 1 (
    echo.
    echo [エラー] GUIの起動に失敗しました。
    echo エラー詳細を確認してください。
    echo.
    pause
) else (
    echo.
    echo GUIを終了しました。
)

pause