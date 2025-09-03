# models/config_models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ProcessingConfig:
    target_images_per_video: int = 330
    cube_resolution: int = 1600
    cuda_enabled: bool = True
    max_iterations: int = 10
    memory_limit_gb: int = 16

@dataclass
class ExtractionConfig:
    base_interval_sec: float = 3.0
    min_interval_sec: float = 1.0
    max_interval_sec: float = 8.0
    direction_offset_range: int = 15
    cube_faces: List[str] = field(default_factory=lambda: ['front', 'back', 'left', 'right', 'up', 'down'])

@dataclass
class PersonFilterConfig:
    confidence_threshold: float = 0.5
    area_ratio_threshold: float = 0.15
    center_distance_threshold: float = 0.3

@dataclass
class YoloFilteringConfig:
    person: PersonFilterConfig = field(default_factory=PersonFilterConfig)
    enabled_classes: List[str] = field(default_factory=lambda: ['person'])

@dataclass
class YoloConfig:
    model_name: str = 'yolov8n.pt'
    device: str = 'cuda'
    filtering: YoloFilteringConfig = field(default_factory=YoloFilteringConfig)

@dataclass
class StopConditionsConfig:
    single_component_threshold: float = 0.95
    reprojection_error_threshold: float = 2.0
    alignment_ratio_threshold: float = 0.95
    improvement_threshold: float = 0.02
    stagnation_iterations: int = 3

@dataclass
class RealityScanConfig:
    executable_path: str = 'RealityScan.exe'
    max_instances: int = 2
    alignment_qualities: List[str] = field(default_factory=lambda: ['draft', 'normal', 'high'])
    stop_conditions: StopConditionsConfig = field(default_factory=StopConditionsConfig)

@dataclass
class OutputConfig:
    generate_colmap: bool = True
    generate_camera_csv: bool = True
    generate_pointcloud: bool = True
    image_format: str = 'jpeg'
    image_quality: int = 95

@dataclass
class LoggingConfig:
    level: str = 'INFO'
    max_log_files: int = 10
    log_rotation_size_mb: int = 100

@dataclass
class AppConfig:
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    yolo: YoloConfig = field(default_factory=YoloConfig)
    realityscan: RealityScanConfig = field(default_factory=RealityScanConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
