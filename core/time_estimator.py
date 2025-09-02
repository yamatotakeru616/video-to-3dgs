# core/time_estimator.py - 処理時間予測
from datetime import datetime, timedelta
from typing import Dict, Any, List
import numpy as np
import logging

class ProcessingTimeEstimator:
    """処理時間予測クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 基準処理時間（秒）
        self.base_times = {
            'frame_extraction': 0.5,    # 秒/フレーム
            'yolo_analysis': 0.1,       # 秒/画像
            'alignment_iteration': 120,  # 秒/反復
            'output_generation': 60     # 秒/処理
        }
        
        # 学習データ
        self.performance_history = []
    
    def estimate_completion_time(self, progress_info: Dict[str, Any], 
                               elapsed_time: timedelta) -> datetime:
        """完了予定時刻予測"""
        current_progress = progress_info['overall_progress']
        
        if current_progress <= 0:
            return datetime.now() + timedelta(hours=2)  # 初期推定
        
        # 現在の処理速度から推定
        rate = current_progress / elapsed_time.total_seconds()
        remaining_progress = 100 - current_progress
        estimated_remaining_seconds = remaining_progress / rate
        
        # 学習データがある場合は補正
        if self.performance_history:
            estimated_remaining_seconds = self._apply_learning_correction(
                estimated_remaining_seconds, progress_info
            )
        
        return datetime.now() + timedelta(seconds=estimated_remaining_seconds)
    
    def update_performance_data(self, phase: str, actual_time: float, 
                              expected_time: float, context: Dict[str, Any]):
        """性能データ更新"""
        self.performance_history.append({
            'phase': phase,
            'actual_time': actual_time,
            'expected_time': expected_time,
            'accuracy': actual_time / expected_time,
            'context': context,
            'timestamp': datetime.now()
        })
    
    def _apply_learning_correction(self, base_estimate: float, 
                                  progress_info: Dict[str, Any]) -> float:
        """学習データによる補正"""
        # 実装: 過去の性能データに基づく予測補正
        pass