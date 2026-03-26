"""配置管理模块 - 统一管理所有配置加载"""
import os
import yaml
from typing import Dict, Any, Optional


# 默认配置文件路径 (基于本文件所在目录)
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "docs_config.yaml"
)


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 验证配置格式
    if not isinstance(config, dict):
        raise ValueError(f"Invalid config format: expected a mapping, got {type(config).__name__}")
    
    return config


def get_doc_source_config(
    source_name: str,
    config_path: str = DEFAULT_CONFIG_PATH
) -> Dict[str, Any]:
    """获取指定文档源的配置"""
    config = load_config(config_path)
    sources = config.get('doc_sources', {})
    
    if source_name not in sources:
        available = list(sources.keys())
        raise ValueError(
            f"Unknown doc source: '{source_name}'. "
            f"Available sources: {available}"
        )
    
    return sources[source_name]


def get_general_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """获取通用配置"""
    config = load_config(config_path)
    return config.get('general', {})


def get_cache_ttl(config_path: str = DEFAULT_CONFIG_PATH) -> int:
    """获取缓存有效期 (秒)"""
    general = get_general_config(config_path)
    return general.get('cache_ttl_seconds', 3600)


def get_default_limit(config_path: str = DEFAULT_CONFIG_PATH) -> int:
    """获取默认返回结果数量"""
    general = get_general_config(config_path)
    return general.get('default_limit', 5)


def get_max_limit(config_path: str = DEFAULT_CONFIG_PATH) -> int:
    """获取最大返回结果数量"""
    general = get_general_config(config_path)
    return general.get('max_limit', 10)
