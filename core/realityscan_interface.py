# core/realityscan_interface.py - RealityScan連携インターフェース
import subprocess
import xml.etree.ElementTree as ET
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import shutil
import os

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
            # NOTE: 実際の実行はコメントアウトし、ダミーのXMLを生成する処理に置き換え
            # result = self._execute_realityscan_commands(commands)
            self._create_dummy_realityscan_output(images, temp_image_dir)
            # 結果解析
            alignment_result = self._parse_alignment_result()

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
        image_dir = self.temp_dir / self.instance_name / 'images'
        image_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"画像を一時ディレクトリにコピー: {image_dir}")
        for img_data in images:
            src_path = Path(img_data['image_path'])
            if src_path.exists():
                shutil.copy(src_path, image_dir / src_path.name)
            else:
                self.logger.warning(f"画像ファイルが見つかりません: {src_path}")
        return image_dir

    def _has_previous_alignment_data(self) -> bool:
        """前回のコンポーネント情報を持っているか"""
        return self.alignment_data is not None

    def _generate_xmp_files(self, images: List[Dict[str, Any]], image_dir: Path):
        """XMPサイドカーファイルの生成"""
        # 実装: 前回のコンポーネント情報を基にXMPファイルを作成
        # TODO: 将来的に実装
        pass

    def _build_alignment_commands(self, image_dir: Path, quality: str) -> List[str]:
        """アライメントCLIコマンド構築"""
        commands = [
            '-headless',
            f'-setInstanceName {self.instance_name}',
            f'-addFolder "{image_dir}"',
            f'-set alignQuality={quality}',
            '-align',
            f'-exportXMP "{self.temp_dir / self.instance_name / "alignment_result.xml"}"',
            f'-exportLatestComponents "{self.temp_dir / self.instance_name / "components"}"'
        ]
        return commands

    def _execute_realityscan_commands(self, commands: List[str]) -> subprocess.CompletedProcess:
        """RealityScanコマンド実行"""
        cmd = [self.realityscan_exe] + commands
        
        self.logger.info(f"RealityScanコマンド実行: {' '.join(cmd)}")
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
            self.logger.error(f"RealityScan実行エラー:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            raise RuntimeError(f"RealityScan実行エラー: {stderr}")
        
        self.logger.info(f"RealityScan出力:\n{stdout}")
        return subprocess.CompletedProcess(cmd, self.current_process.returncode, stdout, stderr)

    def _create_dummy_realityscan_output(self, images: List[Dict[str, Any]], image_dir: Path):
        """ダミーのRealityScan出力XMLを生成する"""
        instance_dir = self.temp_dir / self.instance_name
        instance_dir.mkdir(exist_ok=True)
        xml_path = instance_dir / "alignment_result.xml"

        # シンプルなダミーロジック：
        # 最初の80%の画像を1つのコンポーネントに、残りを未整列とする
        # 2回目以降の実行では、コンポーネントが1つになるように模倣する

        num_images = len(images)
        if self.alignment_data is None: # 初回実行
            num_aligned = int(num_images * 0.8)
            num_components = 2 if num_images > 10 else 1
        else: # 2回目以降
            num_aligned = num_images
            num_components = 1

        root = ET.Element('RealityScanProject')

        # Summary
        summary = ET.SubElement(root, 'summary',
                                total_images=str(num_images),
                                aligned_images=str(num_aligned),
                                mean_reprojection_error="1.85")

        # Components
        components_node = ET.SubElement(root, 'components')
        all_image_paths = [Path(img['image_path']).name for img in images]

        if num_aligned > 0:
            if num_components == 1:
                comp_images = all_image_paths[:num_aligned]
                comp_node = ET.SubElement(components_node, 'component', id='0', num_images=str(len(comp_images)), reprojection_error="1.85")
                for img_name in comp_images:
                    ET.SubElement(comp_node, 'image', path=str(image_dir / img_name), name=img_name)
            else: # 2 component dummy
                comp1_count = num_aligned // 2
                comp2_count = num_aligned - comp1_count

                comp1_images = all_image_paths[:comp1_count]
                comp_node1 = ET.SubElement(components_node, 'component', id='0', num_images=str(len(comp1_images)), reprojection_error="1.9")
                for img_name in comp1_images:
                    ET.SubElement(comp_node1, 'image', path=str(image_dir / img_name), name=img_name)

                comp2_images = all_image_paths[comp1_count:num_aligned]
                comp_node2 = ET.SubElement(components_node, 'component', id='1', num_images=str(len(comp2_images)), reprojection_error="2.1")
                for img_name in comp2_images:
                    ET.SubElement(comp_node2, 'image', path=str(image_dir / img_name), name=img_name)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="\t", level=0)
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        self.logger.info(f"ダミーのXMLファイルを生成しました: {xml_path}")

    def _parse_alignment_result(self) -> Dict[str, Any]:
        """アライメント結果解析"""
        xml_path = self.temp_dir / self.instance_name / "alignment_result.xml"
        if not xml_path.exists():
            self.logger.error(f"アライメント結果のXMLファイルが見つかりません: {xml_path}")
            return self._get_empty_alignment_result()

        self.logger.info(f"XML結果をパース中: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()

        summary = root.find('summary')
        total_images = int(summary.get('total_images', 0))
        aligned_images = int(summary.get('aligned_images', 0))
        mean_reprojection_error = float(summary.get('mean_reprojection_error', 99.0))

        components = []
        aligned_image_names = set()

        for comp_node in root.findall('components/component'):
            comp_id = comp_node.get('id')
            comp_images = []
            for img_node in comp_node.findall('image'):
                img_name = img_node.get('name')
                comp_images.append({
                    'name': img_name,
                    'path': img_node.get('path')
                })
                aligned_image_names.add(img_name)

            components.append({
                'id': comp_id,
                'image_count': int(comp_node.get('num_images', 0)),
                'reprojection_error': float(comp_node.get('reprojection_error', 99.0)),
                'images': comp_images
            })

        # 全画像のリストから未整列の画像を特定
        all_image_files = [p.name for p in (self.temp_dir / self.instance_name / 'images').glob('*.jpg')]
        unaligned_images = [name for name in all_image_files if name not in aligned_image_names]

        return {
            'components': components,
            'total_images': total_images,
            'unaligned_images': unaligned_images,
            'alignment_ratio': (aligned_images / total_images) if total_images > 0 else 0,
            'mean_reprojection_error': mean_reprojection_error,
            'raw_output_path': str(xml_path.parent)
        }

    def _get_empty_alignment_result(self) -> Dict[str, Any]:
        """空のアライメント結果を返す"""
        return {
            'components': [],
            'total_images': 0,
            'unaligned_images': [],
            'alignment_ratio': 0.0,
            'mean_reprojection_error': 99.0, # 高いエラー値
            'raw_output_path': None
        }

    def abort_current_process(self):
        """現在の処理を中断"""
        if self.current_process and self.current_process.poll() is None:
            self.logger.info(f"実行中のRealityScanプロセスを中断します (PID: {self.current_process.pid})")
            self.current_process.terminate()
