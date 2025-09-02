# core/realityscan_interface.py - RealityScan連携インターフェース
import subprocess
import xml.etree.ElementTree as ET
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

class RealityScanInterface:
    """RealityScan CLI連携クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # RealityScan設定
        self.realityscan_exe = config.get('realityscan_executable', 'RealityScan.exe')
        self.temp_dir = Path(tempfile.gettempdir()) / 'video_3dgs_temp'
        self.temp_dir.mkdir(exist_ok=True)
        
        # 処理状態管理
        self.current_process = None
        self.instance_name = f"video3dgs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.alignment_data = None

    def run_alignment(self, images: List[Dict[str, Any]], 
                     quality: str = 'normal') -> Dict[str, Any]:
        """アライメント実行"""
        self.logger.info(f"RealityScanアライメント開始 - {len(images)}枚の画像")
        
        if not images:
            self.logger.warning("画像が0枚のため、アライメントをスキップします。")
            return self._get_empty_alignment_result()

        # 一時画像フォルダ準備
        temp_image_dir = self._prepare_temp_images(images)
        
        # XMPファイル生成
        if self._has_previous_alignment_data():
            self._generate_xmp_files(images, temp_image_dir)
        
        # CLIコマンド構築
        commands = self._build_alignment_commands(temp_image_dir, quality)
        
        # RealityScan実行
        try:
            result = self._execute_realityscan_commands(commands)
            # 結果解析
            alignment_result = self._parse_alignment_result(result)
        except (RuntimeError, FileNotFoundError) as e:
            self.logger.warning(f"RealityScanの実行に失敗しました: {e}。ダミーの結果を返します。")
            # 実行ファイルがない場合などは、ダミーの結果を返す
            alignment_result = self._get_empty_alignment_result()
            alignment_result['total_images'] = len(images)

        self.alignment_data = alignment_result
        self.logger.info(f"アライメント完了 - コンポーネント数: {len(alignment_result['components'])}")
        return alignment_result

    def _prepare_temp_images(self, images: List[Dict[str, Any]]) -> Path:
        """一時画像フォルダ準備"""
        # 実装: 画像を一時フォルダにコピー・整理
        # NOTE: これはプレースホルダー実装です
        image_dir = self.temp_dir / self.instance_name / 'images'
        image_dir.mkdir(parents=True, exist_ok=True)
        return image_dir

    def _has_previous_alignment_data(self) -> bool:
        """前回のコンポーネント情報を持っているか"""
        return self.alignment_data is not None

    def _generate_xmp_files(self, images: List[Dict[str, Any]], image_dir: Path):
        """XMPサイドカーファイルの生成"""
        # 実装: 前回のコンポーネント情報を基にXMPファイルを作成
        pass

    def _build_alignment_commands(self, image_dir: Path, quality: str) -> List[str]:
        """アライメントCLIコマンド構築"""
        commands = [
            '-headless',
            f'-setInstanceName {self.instance_name}',
            f'-addFolder "{image_dir}"',
            f'-set alignQuality={quality}',
            '-align',
            f'-exportXMP "{self.temp_dir / "alignment_result.xml"}"',
            f'-exportLatestComponents "{self.temp_dir / "components"}"'
        ]
        return commands

    def _execute_realityscan_commands(self, commands: List[str]) -> subprocess.CompletedProcess:
        """RealityScanコマンド実行"""
        cmd = [self.realityscan_exe] + commands
        
        # NOTE: 実行ファイルが存在しない場合のエラーハンドリング
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.temp_dir
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"実行ファイルが見つかりません: {self.realityscan_exe}")
        
        stdout, stderr = self.current_process.communicate()
        
        if self.current_process.returncode != 0:
            raise RuntimeError(f"RealityScan実行エラー: {stderr}")
        
        return subprocess.CompletedProcess(cmd, self.current_process.returncode, stdout, stderr)

    def _parse_alignment_result(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """アライメント結果解析"""
        # 実装: XML/JSONからアライメント結果パース
        # NOTE: これはプレースホルダー実装です
        return self._get_empty_alignment_result()

    def _get_empty_alignment_result(self) -> Dict[str, Any]:
        """空のアライメント結果を返す"""
        return {
            'components': [],
            'total_images': 0,
            'alignment_ratio': 0.0,
            'mean_reprojection_error': 99.0, # 高いエラー値
            'raw_output_path': None
        }

    def abort_current_process(self):
        """現在の処理を中断"""
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
