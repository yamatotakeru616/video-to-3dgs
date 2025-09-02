#!/usr/bin/env python3
"""
環境セットアップスクリプト
uv環境でのプロジェクト初期化を自動化
"""

import subprocess
import sys
import os
from pathlib import Path

def setup_project():
    """プロジェクト環境セットアップ"""
    print("=== Video to 3DGS Dataset Generator 環境セットアップ ===")
    
    # 1. uv インストール確認
    if not check_uv_installed():
        print("エラー: uvがインストールされていません")
        return False
    
    # 2. プロジェクトディレクトリ作成
    create_project_structure()
    
    # 3. 依存関係インストール
    install_dependencies()
    
    # 4. YOLOモデルダウンロード
    download_yolo_models()
    
    # 5. 設定ファイル作成
    create_config_files()
    
    print("環境セットアップ完了！")
    return True

def check_uv_installed():
    """uv インストール確認"""
    try:
        subprocess.run(['uv', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_project_structure():
    """プロジェクト構造作成"""
    directories = [
        'src/gui/components',
        'src/core',
        'src/utils',
        'src/models',
        'assets/icons',
        'assets/models',
        'assets/templates',
        'configs/realityscan_templates',
        'tests/fixtures',
        'docs',
        'scripts',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # __init__.py ファイル作成（Pythonパッケージ用）
        if 'src/' in directory:
            init_file = Path(directory) / '__init__.py'
            if not init_file.exists():
                init_file.touch()

def install_dependencies():
    """依存関係インストール"""
    print("依存関係をインストール中...")
    subprocess.run(['uv', 'sync'], check=True)
    subprocess.run(['uv', 'sync', '--extra', 'dev'], check=True)

def download_yolo_models():
    """YOLOモデルダウンロード"""
    print("YOLOモデルをダウンロード中...")
    # 実装: ultralytics経由でのモデルダウンロード
    pass

def create_config_files():
    """設定ファイル作成"""
    # 実装: デフォルト設定ファイルの生成
    pass

if __name__ == "__main__":
    setup_project()