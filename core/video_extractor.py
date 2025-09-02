# core/video_extractor.py の修正

import cv2
import numpy as np
from typing import List, Dict, Any, Optional
# cupy は一旦コメントアウトし、CPUベースで確実に動くようにします
# import cupy as cp 
import logging
from pathlib import Path # Path をインポート

class VideoExtractor:
    """360度動画フレーム抽出クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0 # シンプル化のため一旦コメントアウト
        
        self.extraction_params = {
            'base_interval': 3.0, # 秒
            # ... 他のパラメータ
        }
    
    def extract_adaptive_frames(self, video_path: str, target_count: int, 
                              quality_filter, confidence: float, area_threshold: float) -> List[Dict[str, Any]]:
        """適応的フレーム抽出（基本的な実装を追加）"""
        self.logger.info(f"フレーム抽出開始: {Path(video_path).name}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error(f"動画ファイルを開けませんでした: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        extracted_frames = []
        current_time_sec = 0.0
        
        # 保存先の一時ディレクトリを作成（実装に応じて変更してください）
        # ここでは output_dir の 'temp_images' に保存する仮定で進めます
        output_dir = Path(self.config.get('output_dir', './output')) / 'temp_images'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frame_count = 0
        while current_time_sec < duration and len(extracted_frames) < target_count:
            cap.set(cv2.CAP_PROP_POS_MSEC, int(current_time_sec * 1000))
            ret, frame = cap.read()
            
            if not ret:
                break

            # 品質フィルタリングを実行
            if not quality_filter.is_frame_acceptable(frame, confidence, area_threshold):
                self.logger.debug(f"フレーム {current_time_sec:.2f}s は品質基準を満たさなかったためスキップします。")
                current_time_sec += self.extraction_params['base_interval']
                continue

            # ここでは簡単化のため、6方向抽出ではなく正面のフレームのみを保存します
            # 本来は _extract_directional_frames で6枚の画像を生成します
            
            # 仮実装：全フレームを有効とする
            image_name = f"{Path(video_path).stem}_frame_{frame_count:05d}.jpg"
            image_path = output_dir / image_name
            cv2.imwrite(str(image_path), frame)
            
            frame_data = {
                'video_source': video_path,
                'timestamp': current_time_sec,
                'image_path': str(image_path), # パスを文字列として保存
                # ... 他のメタデータ
            }
            extracted_frames.append(frame_data)
            frame_count += 1
            
            current_time_sec += self.extraction_params['base_interval']

        cap.release()
        self.logger.info(f"フレーム抽出完了: {len(extracted_frames)}枚")
        return extracted_frames

    # 以下、他のメソッドはスケルトンのまま or pass のままでOK
    def _extract_directional_frames(self, cap, timestamp: float, fps: float) -> Dict[str, np.ndarray]:
        pass
    
    def _filter_frames_by_quality(self, frame_data: Dict[str, np.ndarray], 
                                 quality_filter) -> List[Dict[str, Any]]:
        pass
    
    def _extract_with_offset(self, cap, timestamp: float, fps: float, 
                           quality_filter) -> List[Dict[str, Any]]:
        pass
    
    def extract_targeted_frames(self, problem_areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass