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
                              quality_filter) -> List[Dict[str, Any]]:
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

            # ここでは簡単化のため、6方向抽出ではなく正面のフレームのみを保存します
            # 本来は _extract_directional_frames で6枚の画像を生成します
            
            # TODO: ここで品質フィルタリングを実行する
            # valid_frames = self._filter_frames_by_quality(frame, quality_filter)
            # if not valid_frames:
            #     current_time_sec += interval
            #     continue
            
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
        """問題領域からターゲットを絞ってフレームを抽出する"""
        if not problem_areas:
            return []

        self.logger.info(f"{len(problem_areas)}件の問題領域から追加フレームを抽出します。")
        additional_frames = []

        # 問題領域をビデオソースごとにグループ化
        from collections import defaultdict
        problems_by_video = defaultdict(list)
        for problem in problem_areas:
            problems_by_video[problem['video_source']].append(problem)

        # 保存先の一時ディレクトリ
        output_dir = Path(self.config.get('output_dir', './output')) / 'temp_images'
        output_dir.mkdir(parents=True, exist_ok=True)

        # 各ビデオに対して処理
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

                    # ギャップの長さに応じて抽出枚数を決定（例: 1秒あたり3枚）
                    # 最低でも1枚は抽出
                    num_frames_to_extract = max(1, int(duration * 3))

                    self.logger.info(f"  - Problem ({problem['type']}): {start_time:.2f}s - {end_time:.2f}s in {Path(video_path).name}. Extracting {num_frames_to_extract} frames.")

                    if duration <= 0:
                        time_points = [start_time]
                    else:
                        # ギャップ内に均等に配置
                        interval = duration / (num_frames_to_extract + 1)
                        time_points = [start_time + interval * (i + 1) for i in range(num_frames_to_extract)]

                    for t in time_points:
                        cap.set(cv2.CAP_PROP_POS_MSEC, int(t * 1000))
                        ret, frame = cap.read()

                        if not ret:
                            continue

                        # TODO: ここでも品質フィルタリングを適用するのが望ましい

                        # 画像を保存 (ファイル名の衝突を避けるため、タイムスタンプのドットをアンダースコアに置換)
                        image_name = f"{Path(video_path).stem}_targeted_{t:.3f}s.jpg".replace('.', '_')
                        image_path = output_dir / image_name
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