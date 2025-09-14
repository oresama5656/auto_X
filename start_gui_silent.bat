@echo off
REM サイレント起動版 - ターミナルウィンドウを表示しない

chcp 65001 > nul
cd /d "%~dp0"

REM Pythonの存在確認
python --version > nul 2>&1
if errorlevel 1 (
    msg * "エラー: Pythonが見つかりません。Python 3.6以上をインストールしてください。"
    exit /b 1
)

REM GUI起動（バックグラウンド）
start "" pythonw gui.py