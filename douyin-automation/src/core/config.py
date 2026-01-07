"""全局配置管理"""

import json
from pathlib import Path
from typing import Any, Optional


class Config:
    """全局配置类"""

    _instance: Optional['Config'] = None
    _config: dict = {}

    # 默认配置
    DEFAULTS = {
        # 筛选条件
        "filter": {
            "min_rating": 90,           # 最低好评率 %
            "commission_min": 3.5,      # 最低佣金
            "commission_max": 20.0,     # 最高佣金
            "commission_type": "amount", # amount(金额) 或 ratio(比例)
            "price_min": 20.0,          # 最低到手价
            "price_max": 50.0,          # 最高到手价
            "monthly_sales_min": 10000, # 最低月销量
        },
        # 抖音视频筛选
        "douyin_video": {
            "min_duration": 45.0,       # 最短时长(秒)
            "max_duration": 80.0,       # 最长时长(秒)
            "min_likes": 1000,          # 最低点赞数
            "download_count": 5,        # 下载数量
            "scroll_times": 3,          # 搜索页滚动次数
        },
        # 剪映设置
        "jianying": {
            "app_path": "",             # 剪映应用路径
            "template_dir": "",         # 模板目录
            "draft_dir": "",            # 草稿目录
            "export_timeout": 1200,     # 导出超时(秒)
        },
        # 豆包API
        "doubao": {
            "api_key": "",
            "model": "doubao-1-5-pro-32k",
            "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        },
        # 输出设置
        "output": {
            "base_dir": "",             # 输出根目录
        },
        # 服务器设置
        "server": {
            "port": 5000,
            "host": "127.0.0.1",
        },
        # 浏览器设置
        "browser": {
            "headless": False,
            "debug": True,
        },
        # 选品设置
        "picking": {
            "product_count": 3,     # 要选择的产品数量 N
        },
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self._config_path = self._get_config_path()
            self._load_config()

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        # 默认在 config 目录下
        base_dir = Path(__file__).parent.parent.parent / "config"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / "settings.json"

    def _load_config(self) -> None:
        """加载配置文件"""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}

        # 合并默认配置
        self._config = self._merge_defaults(self.DEFAULTS, self._config)
        self.save()

    def _merge_defaults(self, defaults: dict, config: dict) -> dict:
        """递归合并默认配置"""
        result = defaults.copy()
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_defaults(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号分隔的路径

        例如: config.get("filter.min_rating")
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置项，支持点号分隔的路径"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self) -> None:
        """保存配置到文件"""
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    @property
    def all(self) -> dict:
        """获取所有配置"""
        return self._config.copy()

    def reset(self) -> None:
        """重置为默认配置"""
        self._config = self.DEFAULTS.copy()
        self.save()
