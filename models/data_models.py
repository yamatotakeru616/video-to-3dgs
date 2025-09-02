# models/data_models.py - データモデル定義
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

@dataclass
class VideoData:
    """動画データモデル"""
    path: Path
    fps: float
    duration: float
    total_frames: int
    resolution: Tuple[int, int]
    
    def __post_init__(self):
        self.name = self.path.name

@dataclass
class FrameData:
    """フレームデータモデル"""
    video_source: str
    timestamp: float
    direction: str
    image_path: Path
    quality_score: float
    yolo_detections: List[Dict[str, Any]]
    is_valid: bool
    rejection_reason: Optional[str] = None

@dataclass
class AlignmentResult:
    """アライメント結果モデル"""
    iteration: int
    total_images: int
    aligned_images: int
    components: List[Dict[str, Any]]
    mean_reprojection_error: float
    alignment_ratio: float
    processing_time: float
    
    @property
    def component_count(self) -> int:
        return len(self.components)

@dataclass
class ComponentAnalysis:
    """コンポーネント解析結果"""
    component_id: int
    image_count: int
    coverage_areas: List[str]
    quality_metrics: Dict[str, float]
    connection_strength: float
    problem_areas: List[Dict[str, Any]]

@dataclass
class ProcessingProgress:
    """処理進捗データ"""
    overall_progress: float
    phase_progress: float
    current_phase: str
    iteration_count: int
    total_images: int
    start_time: datetime
    estimated_completion: Optional[datetime] = None