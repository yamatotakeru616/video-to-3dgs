# core/video_extractor.py の修正

import cv2
import numpy as np
from typing import List, Dict, Any, Optional
# cupy は一旦コメントアウトし、CPUベースで確実に動くようにします
# import cupy as cp 
import logging
from pathlib import Path # Path をインポート

from models.config_models import AppConfig
from .quality_filter import QualityFilter

class VideoExtractor:
    """360度動画フレーム抽出クラス"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def extract_adaptive_frames(self, video_path: str, target_count: int, 
                              quality_filter: QualityFilter, confidence: float, 
                              area_threshold: float, output_dir: str) -> List[Dict[str, Any]]:
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
        
        temp_image_dir = Path(output_dir) / 'temp_images'
        temp_image_dir.mkdir(parents=True, exist_ok=True)
        
        frame_count = 0
        base_interval = self.config.extraction.base_interval_sec

        while current_time_sec < duration and len(extracted_frames) < target_count:
            cap.set(cv2.CAP_PROP_POS_MSEC, int(current_time_sec * 1000))
            ret, frame = cap.read()
            
            if not ret:
                break

            # 品質フィルタリングを実行
            if not quality_filter.is_frame_acceptable(frame, confidence, area_threshold):
                self.logger.debug(f"フレーム {current_time_sec:.2f}s は品質基準を満たさなかったためスキップします。")
                current_time_sec += base_interval
                continue

            image_name = f"{Path(video_path).stem}_frame_{frame_count:05d}.jpg"
            image_path = temp_image_dir / image_name
            cv2.imwrite(str(image_path), frame)
            
            frame_data = {
                'video_source': video_path,
                'timestamp': current_time_sec,
                'image_path': str(image_path),
            }
            extracted_frames.append(frame_data)
            frame_count += 1
            
            current_time_sec += base_interval

        cap.release()
        self.logger.info(f"フレーム抽出完了: {len(extracted_frames)}枚")
        return extracted_frames

    def extract_targeted_frames(self, problem_areas: List[Dict[str, Any]], output_dir: str) -> List[Dict[str, Any]]:
        """問題領域からターゲットを絞ってフレームを抽出する"""
        if not problem_areas:
            return []

        self.logger.info(f"{len(problem_areas)}件の問題領域から追加フレームを抽出します。")
        additional_frames = []

        from collections import defaultdict
        problems_by_video = defaultdict(list)
        for problem in problem_areas:
            problems_by_video[problem['video_source']].append(problem)

        temp_image_dir = Path(output_dir) / 'temp_images'
        temp_image_dir.mkdir(parents=True, exist_ok=True)

        for video_path, problems in problems_by_video.items():
            try:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.logger.error(f"動画ファイルを開けませんでした: {video_path}")
                    continue

                for problem in problems:
                    start_time = problem['start_time']
                    end_time = problem['end_time']
                    duration = end_time - start_time

                    num_frames_to_extract = max(1, int(duration * 3))

                    self.logger.info(f"  - Problem ({problem['type']}): {start_time:.2f}s - {end_time:.2f}s in {Path(video_path).name}. Extracting {num_frames_to_extract} frames.")

                    if duration <= 0:
                        time_points = [start_time]
                    else:
                        interval = duration / (num_frames_to_extract + 1)
                        time_points = [start_time + interval * (i + 1) for i in range(num_frames_to_extract)]

                    for t in time_points:
                        cap.set(cv2.CAP_PROP_POS_MSEC, int(t * 1000))
                        ret, frame = cap.read()

                        if not ret:
                            continue

                        image_name = f"{Path(video_path).stem}_targeted_{f'{t:.3f}'.replace('.', '_')}s.jpg"
                        image_path = temp_image_dir / image_name
                        cv2.imwrite(str(image_path), frame)

                        frame_data = {
                            'video_source': video_path,
                            'timestamp': t,
                            'image_path': str(image_path),
                            'type': 'targeted'
                        }
                        additional_frames.append(frame_data)
            finally:
                if cap and cap.isOpened():
                    cap.release()

        self.logger.info(f"ターゲットフレーム抽出完了: {len(additional_frames)}枚")
        return additional_frames
