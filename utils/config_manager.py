# utils/config_manager.py
import yaml
from pathlib import Path
from typing import Dict, Any, TypeVar, Type
import logging
from models.config_models import AppConfig

T = TypeVar('T')

def _from_dict(data_class: Type[T], data: Dict[str, Any]) -> T:
    """Recursively create a dataclass instance from a dictionary."""
    if not hasattr(data_class, '__dataclass_fields__'):
        return data
    
    field_types = {f.name: f.type for f in data_class.__dataclass_fields__.values()}
    
    return data_class(**{
        f: _from_dict(field_types[f], data[f])
        for f in data
        if f in field_types
    })

def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = _merge_dicts(base[key], value)
        else:
            base[key] = value
    return base

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        self.default_config_path = self.config_dir / "default_config.yaml"
        self.user_config_path = self.config_dir / "user_config.yaml"

    def load_config(self) -> AppConfig:
        """設定ファイルを読み込み、マージしてAppConfigオブジェクトを返す"""
        # 1. デフォルト設定を読み込む
        if not self.default_config_path.exists():
            self.logger.error(f"デフォルト設定ファイルが見つかりません: {self.default_config_path}")
            # デフォルトがない場合は、dataclassのデフォルト値でAppConfigを生成
            return AppConfig()
        
        with open(self.default_config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 2. ユーザー設定が存在すれば読み込んでマージする
        if self.user_config_path.exists():
            self.logger.info(f"ユーザー設定ファイルを読み込みます: {self.user_config_path}")
            with open(self.user_config_path, 'r', encoding='utf-8') as f:
                user_config_data = yaml.safe_load(f)
            
            if user_config_data:
                config_data = _merge_dicts(config_data, user_config_data)
        
        # 3. 辞書からAppConfigオブジェクトを生成
        try:
            return _from_dict(AppConfig, config_data)
        except (TypeError, KeyError) as e:
            self.logger.error(f"設定ファイルからAppConfigの生成に失敗しました: {e}")
            self.logger.error("設定ファイルのキーが不正か、値の型が間違っている可能性があります。")
            # パース失敗時はデフォルトのAppConfigを返す
            return AppConfig()

    def save_config(self, config: Dict[str, Any], config_name: str = "user_config.yaml"):
        """設定ファイル保存"""
        config_path = self.config_dir / config_name
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
