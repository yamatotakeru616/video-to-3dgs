# core/output_generator.py - 3DGS用出力生成
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
import json
from typing import Dict, List, Any
import logging

class OutputGenerator:
    """3D Gaussian Splatting用データ出力クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_3dgs_dataset(self, alignment_result: Dict[str, Any], 
                             output_dir: str) -> Dict[str, Any]:
        """3DGSデータセット生成"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        self.logger.info(f"3DGSデータセット生成開始: {output_path}")
        
        # 出力フォルダ構造作成
        dataset_structure = self._create_dataset_structure(output_path)
        
        # 各形式でのデータ出力
        results = {}
        
        # 1. COLMAP形式出力
        results['colmap'] = self._generate_colmap_data(alignment_result, dataset_structure['sparse'])
        
        # 2. カメラパラメータCSV出力（PostShot用）
        results['camera_csv'] = self._generate_camera_csv(alignment_result, dataset_structure['root'])
        
        # 3. 点群PLY出力
        results['pointcloud'] = self._generate_point_cloud(alignment_result, dataset_structure['dense'])
        
        # 4. 画像整理・コピー
        # The user's provided code assumes the key is 'images', but the processing_engine
        # passes the whole alignment_result. Let's pass the correct part.
        # The `run_alignment` in realityscan_interface returns a dict that contains the images.
        # Let's assume the images are in alignment_result['images'] for now.
        results['images'] = self._organize_images(alignment_result, dataset_structure['images'])
        
        # 5. メタデータ出力
        results['metadata'] = self._generate_metadata(alignment_result, dataset_structure['root'])
        
        self.logger.info("3DGSデータセット生成完了")
        return {
            'output_path': str(output_path),
            'results': results,
            'structure': dataset_structure
        }
    
    def _create_dataset_structure(self, base_path: Path) -> Dict[str, Path]:
        """データセット フォルダ構造作成"""
        structure = {
            'root': base_path,
            'images': base_path / 'images',
            'sparse': base_path / 'sparse',
            'dense': base_path / 'dense',
            'logs': base_path / 'logs'
        }
        
        for folder in structure.values():
            folder.mkdir(exist_ok=True)
        
        return structure

    def _generate_colmap_data(self, alignment_result: Dict[str, Any], sparse_dir: Path) -> Dict[str, str]:
        """COLMAP形式データ生成"""
        # 実装: cameras.txt, images.txt, points3D.txt生成
        self.logger.info(f"COLMAPデータを {sparse_dir} に生成中... (スキップ)")
        return "Skipped"
    
    def _generate_camera_csv(self, alignment_result: Dict[str, Any], output_dir: Path) -> str:
        """カメラパラメータCSV生成（PostShot用）"""
        # 実装: camera_params.csv生成
        self.logger.info(f"カメラパラメータCSVを {output_dir} に生成中... (スキップ)")
        return "Skipped"
    
    def _generate_point_cloud(self, alignment_result: Dict[str, Any], dense_dir: Path) -> str:
        """点群PLY生成"""
        # 実装: 点群データをPLY形式で出力
        self.logger.info(f"点群PLYを {dense_dir} に生成中... (スキップ)")
        return "Skipped"

    def _organize_images(self, alignment_result: Dict[str, Any], images_dir: Path) -> str:
        """アライメントに使用された画像をimagesフォルダにコピーする"""
        self.logger.info(f"画像を {images_dir} に整理中...")
        
        # The list of image dictionaries is what we get from video_extractor
        # and is passed through the processing_engine. It's the top-level object.
        image_list = alignment_result.get('aligned_images', []) # Assuming this key exists
        if not image_list:
            # Fallback for the case where the key is not present, use the root list if it's a list of dicts
            if isinstance(alignment_result, list):
                 image_list = alignment_result
            else: # Or maybe it's in the 'images' key from the start
                 image_list = alignment_result.get('images', [])

        if not image_list or not isinstance(image_list, list):
            self.logger.warning("整理対象の画像リストが見つからないか、形式が不正です。")
            return "No valid image list found to organize."
            
        count = 0
        for image_info in image_list:
            if isinstance(image_info, dict) and 'image_path' in image_info:
                source_path = Path(image_info['image_path'])
                if source_path.exists():
                    shutil.copy(source_path, images_dir)
                    count += 1
            else:
                self.logger.warning(f"無効な画像情報が見つかりました: {image_info}")
        
        self.logger.info(f"{count}枚の画像をコピーしました。")
        return f"Copied {count} images."

    def _generate_metadata(self, alignment_result: Dict[str, Any], output_dir: Path) -> str:
        """メタデータJSON出力"""
        metadata_path = output_dir / 'metadata.json'
        self.logger.info(f"メタデータを {metadata_path} に出力中...")
        try:
            # Create a serializable version of the alignment result
            serializable_result = {
                k: v for k, v in alignment_result.items() 
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))
            }
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, indent=4, ensure_ascii=False)
            return str(metadata_path)
        except Exception as e:
            self.logger.error(f"メタデータの保存中にエラーが発生しました: {e}")
            return f"Error saving metadata: {e}"
