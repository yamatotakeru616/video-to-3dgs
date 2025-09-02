# utils/cuda_utils.py - CUDA関連ユーティリティ
import cv2
import cupy as cp
import torch
import numpy as np
from typing import Optional, Tuple
import logging

class CudaUtils:
    """CUDA処理ユーティリティクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cuda_available = self._check_cuda_availability()
    
    def _check_cuda_availability(self) -> bool:
        """CUDA利用可能性チェック"""
        checks = {
            'opencv_cuda': cv2.cuda.getCudaEnabledDeviceCount() > 0,
            'cupy': cp.cuda.is_available(),
            'torch_cuda': torch.cuda.is_available()
        }
        
        self.logger.info(f"CUDA利用可能性: {checks}")
        return all(checks.values())
    
    def equirect_to_cube_gpu(self, equirect_image: np.ndarray, 
                           direction: str) -> Optional[np.ndarray]:
        """GPU使用 正距円筒図→キューブマップ変換"""
        if not self.cuda_available:
            return self._equirect_to_cube_cpu(equirect_image, direction)
        
        # 実装: CUDA使用の高速変換処理
        pass
    
    def batch_image_processing_gpu(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """バッチ画像処理（GPU）"""
        # 実装: 複数画像の並列GPU処理
        pass