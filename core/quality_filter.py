# core/quality_filter.py - YOLO画像品質フィルタ
import torch
from ultralytics import YOLO
import cv2
import numpy as np
from typing import Dict, List, Any, Tuple
import logging

from models.config_models import YoloConfig

class QualityFilter:
    """YOLO画像品質フィルタリングクラス"""
    
    def __init__(self, config: YoloConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # YOLOモデル初期化
        self.logger.info(f"YOLOモデルを読み込んでいます: {self.config.model_name}")
        try:
            self.model = YOLO(self.config.model_name)
            if torch.cuda.is_available() and self.config.device == 'cuda':
                self.logger.info("CUDAが利用可能です。モデルをGPUに転送します。")
                self.model.to('cuda')
            else:
                self.logger.info("CUDAが利用不可、または設定で無効化されています。CPUで実行します。")
        except Exception as e:
            self.logger.error(f"YOLOモデルの読み込みに失敗しました: {e}")
            raise

    def is_frame_acceptable(self, image: np.ndarray, confidence_threshold: float, area_ratio_threshold: float) -> bool:
        """フレームが品質基準を満たしているか判定する"""
        if image is None:
            return False

        img_height, img_width, _ = image.shape
        total_area = img_width * img_height

        # YOLOで推論実行
        results = self.model(image, verbose=False) # verbose=Falseでログ出力を抑制

        for result in results:
            # Person class is 0 in COCO dataset
            person_detections = result.boxes.data[result.boxes.data[:, -1] == 0]

            for det in person_detections:
                conf = det[4].item()
                if conf >= confidence_threshold:
                    # バウンディングボックスの面積計算
                    x1, y1, x2, y2 = det[:4]
                    box_width = x2 - x1
                    box_height = y2 - y1
                    box_area = box_width * box_height
                    
                    # 面積比チェック
                    area_ratio = box_area / total_area
                    if area_ratio >= area_ratio_threshold:
                        self.logger.debug(f"フレーム却下: 人物検出 (信頼度: {conf:.2f}, 面積比: {area_ratio:.2f}) が閾値を超えました")
                        return False # 基準を満たさない

        return True # すべてのチェックをパス

    def update_filter_settings(self, new_settings: Dict[str, Any]):
        """フィルタ設定更新 (現在は未使用)"""
        # このメソッドは現在直接は使われないが、将来的な拡張のために残す
        pass