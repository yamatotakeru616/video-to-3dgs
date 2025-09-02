# utils/config_manager.py - 設定管理
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_name: str = "default_config.yaml") -> Dict[str, Any]:
        """設定ファイル読み込み"""
        config_path = self.config_dir / config_name
        
        if not config_path.exists():
            self.logger.warning(f"設定ファイルが見つかりません: {config_path}")
            return self._get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def save_config(self, config: Dict[str, Any], config_name: str = "user_config.yaml"):
        """設定ファイル保存"""
        config_path = self.config_dir / config_name
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            'processing': {
                'target_images_per_video': 330,
                'cube_resolution': 1600,
                'cuda_enabled': True,
                'max_iterations': 10
            },
            'extraction': {
                'base_interval_sec': 3.0,
                'min_interval_sec': 1.0,
                'max_interval_sec': 8.0,
                'direction_offset_range': 15
            },
            'yolo': {
                'model_name': 'yolov8n.pt',
                'person_confidence': 0.5,
                'area_threshold': 0.15
            },
            'realityscan': {
                'executable_path': '',
                'max_instances': 2,
                'alignment_quality': 'high'
            },
            'output': {
                'generate_colmap': True,
                'generate_camera_csv': True,
                'generate_pointcloud': True,
                'image_format': 'jpeg',
                'image_quality': 95
            }
        }