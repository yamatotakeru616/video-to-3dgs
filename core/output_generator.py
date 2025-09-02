# core/output_generator.py - 3DGS用出力生成
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
import json
from typing import Dict, List, Any
import logging
import cv2

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
        results['images'] = self._organize_images(alignment_result, dataset_structure['images'])
        
        # 5. メタデータ出力
        results['metadata'] = self._generate_metadata(alignment_result, dataset_structure['root'])
        
        # 6. 正距円筒図の画像を生成
        results['equirectangular'] = self._generate_equirectangular_image(alignment_result, dataset_structure['root'])

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
        
        image_list = alignment_result.get('aligned_images', [])
        if not image_list:
            if isinstance(alignment_result, list):
                 image_list = alignment_result
            else:
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

    def _generate_equirectangular_image(self, alignment_result: Dict[str, Any], output_dir: Path) -> str:
        """正距円筒図の画像を生成"""
        self.logger.info(f"正距円筒図の画像を {output_dir} に生成中...")

        # 1. 必要なデータを抽出
        components = alignment_result.get('components', [])
        if not components:
            self.logger.warning("アライメントされたコンポーネントが見つからないため、正距円筒図を生成できません。")
            return "Skipped (no components)"

        # 最大のコンポーネントを選択
        main_component = max(components, key=lambda c: c['image_count'])
        images_data = main_component.get('images', [])
        if not images_data:
            self.logger.warning("コンポーネントに画像情報がないため、正距円筒図を生成できません。")
            return "Skipped (no images in component)"

        # 2. カメラの内部・外部パラメータと画像パスを準備
        try:
            first_image = cv2.imread(images_data[0]['path'])
            if first_image is None:
                raise FileNotFoundError(f"画像ファイルが読み込めません: {images_data[0]['path']}")
            img_h, img_w, _ = first_image.shape

            # 視野角90度を仮定して焦点距離を計算
            fov_x_rad = np.radians(90)
            focal_length = (img_w / 2) / np.tan(fov_x_rad / 2)
            K = np.array([[focal_length, 0, img_w / 2], [0, focal_length, img_h / 2], [0, 0, 1]])

            cameras = []
            for img_data in images_data:
                R_cw = np.array(img_data['pose']['rotation'])
                C_w = np.array([img_data['pose']['tx'], img_data['pose']['ty'], img_data['pose']['tz']])
                R_wc = R_cw.T
                t_wc = -R_wc @ C_w
                cameras.append({'path': img_data['path'], 'R': R_wc, 't': t_wc, 'C': C_w, 'view_dir': R_cw[:, 2]})
        except (KeyError, IndexError, FileNotFoundError) as e:
            self.logger.error(f"カメラパラメータの準備中にエラー: {e}")
            return f"Skipped (error preparing camera data: {e})"

        # 3. 正距円筒図のキャンバスを作成
        eq_w, eq_h = 4096, 2048
        equirectangular_image = np.zeros((eq_h, eq_w, 3), dtype=np.uint8)

        # 4. 逆マッピングで画像を生成
        self.logger.info("逆マッピングによる画像生成を開始...")
        u_eq, v_eq = np.meshgrid(np.arange(eq_w), np.arange(eq_h))

        theta = (u_eq / eq_w - 0.5) * 2 * np.pi
        phi = (v_eq / eq_h - 0.5) * np.pi

        # 球面座標から3Dベクトルへ
        d_world_x = np.cos(phi) * np.sin(theta)
        d_world_y = -np.sin(phi)
        d_world_z = np.cos(phi) * np.cos(theta)
        d_world = np.stack([d_world_x, d_world_y, d_world_z], axis=-1)

        # 各ピクセルに最適なカメラを見つける
        best_cam_indices = np.zeros((eq_h, eq_w), dtype=int)
        max_dot = np.full((eq_h, eq_w), -1.0, dtype=float)

        for i, cam in enumerate(cameras):
            # カメラビュー方向とピクセル方向のドット積を計算
            dot_product = np.einsum('ij,hwj->hw', cam['view_dir'][np.newaxis, :], d_world)
            # より最適なカメラであれば更新
            mask = dot_product > max_dot
            max_dot[mask] = dot_product[mask]
            best_cam_indices[mask] = i

        # 5. 各カメラからピクセルをサンプリング
        self.logger.info("各カメラからのピクセルサンプリングを開始...")
        for i, cam in enumerate(cameras):
            mask = best_cam_indices == i
            if not np.any(mask):
                continue

            d_world_cam = d_world[mask]
            d_cam = (cam['R'] @ d_world_cam.T).T

            # 3D点を画像平面に投影
            x_proj = d_cam[:, 0] / d_cam[:, 2]
            y_proj = d_cam[:, 1] / d_cam[:, 2]

            u_img = K[0, 0] * x_proj + K[0, 2]
            v_img = K[1, 1] * y_proj + K[1, 2]

            # 画像境界内のピクセルのみを対象
            valid_mask = (u_img >= 0) & (u_img < img_w) & (v_img >= 0) & (v_img < img_h)
            
            if not np.any(valid_mask):
                continue

            # 元画像から色をサンプリング (最近傍補間)
            source_image = cv2.imread(cam['path'])
            u_img_valid = u_img[valid_mask].astype(int)
            v_img_valid = v_img[valid_mask].astype(int)
            colors = source_image[v_img_valid, u_img_valid]

            # キャンバスに描画
            eq_coords = np.argwhere(mask)
            eq_coords_valid = eq_coords[valid_mask]
            equirectangular_image[eq_coords_valid[:, 0], eq_coords_valid[:, 1]] = colors

        # 6. 結果を保存
        output_path = output_dir / "equirectangular.jpg"
        self.logger.info(f"正距円筒図を保存中: {output_path}")
        cv2.imwrite(str(output_path), equirectangular_image)

        return str(output_path)
