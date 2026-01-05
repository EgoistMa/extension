"""视频数据模型"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Video:
    """抖音视频信息"""

    # 基础信息
    video_id: str                       # 视频ID
    title: str                          # 视频标题
    url: str                            # 视频URL

    # 作者信息
    author_id: str = ""                 # 作者ID
    author_name: str = ""               # 作者昵称
    author_url: str = ""                # 作者主页

    # 视频属性
    duration: float = 0.0               # 时长(秒)
    width: int = 0                      # 宽度
    height: int = 0                     # 高度

    # 互动数据
    likes: int = 0                      # 点赞数
    comments: int = 0                   # 评论数
    shares: int = 0                     # 分享数
    plays: int = 0                      # 播放数

    # 下载信息
    download_url: str = ""              # 无水印下载地址
    local_path: str = ""                # 本地路径
    is_downloaded: bool = False         # 是否已下载

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    publish_time: str = ""              # 发布时间
    source: str = "douyin"              # 来源平台

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Video':
        """从字典创建"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def save(self, path: Path) -> None:
        """保存到JSON文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'Video':
        """从JSON文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def meets_criteria(
        self,
        min_duration: float = 0,
        max_duration: float = float('inf'),
        min_likes: int = 0
    ) -> bool:
        """检查是否满足筛选条件

        Args:
            min_duration: 最短时长(秒)
            max_duration: 最长时长(秒)
            min_likes: 最低点赞数

        Returns:
            是否满足条件
        """
        if self.duration < min_duration or self.duration > max_duration:
            return False

        if self.likes < min_likes:
            return False

        return True


@dataclass
class ExportedVideo:
    """导出的视频信息"""

    # 基础信息
    video_id: str                       # 视频ID (关联Project)
    local_path: str                     # 本地路径

    # 视频属性
    duration: float = 0.0               # 时长(秒)
    file_size: int = 0                  # 文件大小(字节)

    # 发布信息
    title: str = ""                     # 发布标题
    description: str = ""               # 发布描述
    tags: list = field(default_factory=list)  # 标签列表

    # 上传状态
    is_uploaded: bool = False           # 是否已上传
    upload_url: str = ""                # 上传后的视频URL
    uploaded_at: str = ""               # 上传时间

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_videos: list = field(default_factory=list)  # 源视频ID列表

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ExportedVideo':
        """从字典创建"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
