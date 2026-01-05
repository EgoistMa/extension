#!/usr/bin/env python3
"""
项目配置管理器
管理每个下载项目的状态和配置
"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from enum import Enum


class ProjectStatus(str, Enum):
    """项目状态"""
    PENDING = "pending"           # 等待中
    SEARCHING = "searching"       # 搜索视频中
    DOWNLOADING = "downloading"   # 下载中
    DOWNLOAD_DONE = "download_done"  # 下载完成
    EDITING = "editing"           # 剪辑中
    EDIT_DONE = "edit_done"       # 剪辑完成
    UPLOADING = "uploading"       # 上传中
    UPLOAD_DONE = "upload_done"   # 上传完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class VideoStatus(str, Enum):
    """视频状态"""
    FOUND = "found"               # 已找到
    FILTERED = "filtered"         # 已筛选（符合条件）
    DOWNLOADING = "downloading"   # 下载中
    DOWNLOADED = "downloaded"     # 已下载
    FAILED = "failed"             # 下载失败
    SKIPPED = "skipped"           # 跳过


@dataclass
class VideoItem:
    """视频项"""
    aweme_id: str                 # 视频ID
    url: str                      # 视频页面URL
    video_url: str = ""           # 视频下载URL
    author: str = ""              # 作者
    title: str = ""               # 标题
    duration: float = 0           # 时长（秒）
    digg_count: int = 0           # 点赞数
    comment_count: int = 0        # 评论数
    share_count: int = 0          # 分享数
    status: str = VideoStatus.FOUND
    local_path: str = ""          # 本地文件路径
    error_message: str = ""       # 错误信息
    downloaded_at: str = ""       # 下载时间

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoItem':
        return cls(**data)


@dataclass
class ProjectConfig:
    """项目配置"""
    # 基本信息
    project_id: str               # 项目ID（使用时间戳）
    product_name: str             # 产品名称
    search_keyword: str           # 搜索关键词
    created_at: str               # 创建时间
    updated_at: str               # 更新时间

    # 项目路径
    project_dir: str              # 项目目录
    videos_dir: str = ""          # 视频保存目录

    # 状态
    status: str = ProjectStatus.PENDING
    retry_count: int = 0          # 重试次数

    # 产品信息（来自百应）
    commission_rate: str = ""     # 佣金比例
    commission_amount: str = ""   # 佣金金额
    price: str = ""               # 价格
    monthly_sales: str = ""       # 月销量
    shop_score: str = ""          # 店铺评分
    total_score: float = 0        # 综合得分

    # 筛选设置
    filter_settings: Dict = field(default_factory=dict)

    # 视频列表
    found_videos: List[Dict] = field(default_factory=list)      # 搜索找到的视频
    filtered_videos: List[Dict] = field(default_factory=list)   # 筛选后的视频
    downloaded_videos: List[Dict] = field(default_factory=list) # 已下载的视频

    # 剪映项目
    jianying_project_path: str = ""   # 剪映项目路径
    jianying_created_at: str = ""     # 剪映项目创建时间

    # 抖音上传（预留）
    douyin_upload_status: str = ""    # 上传状态
    douyin_video_id: str = ""         # 抖音视频ID
    douyin_uploaded_at: str = ""      # 上传时间

    # 错误信息
    error_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ProjectConfig':
        # 处理默认值
        data.setdefault('filter_settings', {})
        data.setdefault('found_videos', [])
        data.setdefault('filtered_videos', [])
        data.setdefault('downloaded_videos', [])
        return cls(**data)

    def save(self):
        """保存配置到文件"""
        self.updated_at = datetime.now().isoformat()
        config_path = Path(self.project_dir) / "project_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, project_dir: str) -> Optional['ProjectConfig']:
        """从文件加载配置"""
        config_path = Path(project_dir) / "project_config.json"
        if not config_path.exists():
            return None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"加载项目配置失败: {e}")
            return None


class ProjectManager:
    """项目管理器"""

    def __init__(self, base_dir: str):
        """
        初始化项目管理器

        Args:
            base_dir: 项目基础目录（如 C:/Users/xxx/Downloads/baiying_videos）
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_project(
        self,
        product_name: str,
        product_data: dict = None,
        filter_settings: dict = None
    ) -> ProjectConfig:
        """
        创建新项目

        Args:
            product_name: 产品名称
            product_data: 产品数据（来自百应）
            filter_settings: 筛选设置

        Returns:
            ProjectConfig 对象
        """
        now = datetime.now()
        project_id = now.strftime('%Y%m%d_%H%M%S')
        timestamp = now.strftime('%m%d_%H%M%S')

        # 生成安全的文件名
        safe_name = self._safe_filename(product_name[:30])
        project_dir_name = f"{safe_name}_{timestamp}"
        project_dir = self.base_dir / project_dir_name

        # 创建项目配置
        config = ProjectConfig(
            project_id=project_id,
            product_name=product_name,
            search_keyword=product_name[:20],
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            project_dir=str(project_dir),
            videos_dir=str(project_dir),
            status=ProjectStatus.PENDING,
            filter_settings=filter_settings or {}
        )

        # 添加产品数据
        if product_data:
            config.commission_rate = product_data.get('commission_rate', '')
            config.commission_amount = product_data.get('commission_amount', '')
            config.price = product_data.get('price', '')
            config.monthly_sales = product_data.get('monthly_sales', '')
            config.shop_score = product_data.get('shop_score', '')
            config.total_score = product_data.get('totalScore', 0)

        # 保存配置
        config.save()

        return config

    def get_project(self, project_dir: str) -> Optional[ProjectConfig]:
        """获取项目配置"""
        return ProjectConfig.load(project_dir)

    def list_projects(self) -> List[ProjectConfig]:
        """
        列出所有项目

        Returns:
            项目列表，按创建时间倒序
        """
        projects = []

        for item in self.base_dir.iterdir():
            if item.is_dir():
                config = ProjectConfig.load(str(item))
                if config:
                    projects.append(config)

        # 按创建时间倒序
        projects.sort(key=lambda x: x.created_at, reverse=True)
        return projects

    def get_incomplete_projects(self) -> List[ProjectConfig]:
        """
        获取未完成的项目

        Returns:
            未完成的项目列表
        """
        incomplete_statuses = [
            ProjectStatus.PENDING,
            ProjectStatus.SEARCHING,
            ProjectStatus.DOWNLOADING,
            ProjectStatus.DOWNLOAD_DONE,
            ProjectStatus.EDITING,
        ]

        projects = self.list_projects()
        return [p for p in projects if p.status in incomplete_statuses]

    def update_project_status(
        self,
        project_dir: str,
        status: ProjectStatus,
        error_message: str = None
    ):
        """更新项目状态"""
        config = self.get_project(project_dir)
        if config:
            config.status = status
            if error_message:
                config.error_message = error_message
            config.save()

    def add_found_videos(self, project_dir: str, videos: List[VideoItem]):
        """添加搜索到的视频"""
        config = self.get_project(project_dir)
        if config:
            config.found_videos = [v.to_dict() if isinstance(v, VideoItem) else v for v in videos]
            config.status = ProjectStatus.SEARCHING
            config.save()

    def add_filtered_videos(self, project_dir: str, videos: List[VideoItem]):
        """添加筛选后的视频"""
        config = self.get_project(project_dir)
        if config:
            config.filtered_videos = [v.to_dict() if isinstance(v, VideoItem) else v for v in videos]
            config.save()

    def update_video_status(
        self,
        project_dir: str,
        aweme_id: str,
        status: VideoStatus,
        local_path: str = None,
        error_message: str = None
    ):
        """更新视频状态"""
        config = self.get_project(project_dir)
        if not config:
            return

        # 在 filtered_videos 中查找并更新
        for video in config.filtered_videos:
            if video.get('aweme_id') == aweme_id:
                video['status'] = status
                if local_path:
                    video['local_path'] = local_path
                    video['downloaded_at'] = datetime.now().isoformat()
                if error_message:
                    video['error_message'] = error_message
                break

        # 如果下载成功，添加到已下载列表
        if status == VideoStatus.DOWNLOADED and local_path:
            video_item = next(
                (v for v in config.filtered_videos if v.get('aweme_id') == aweme_id),
                None
            )
            if video_item and video_item not in config.downloaded_videos:
                config.downloaded_videos.append(video_item)

        config.save()

    def set_jianying_project(self, project_dir: str, jianying_path: str):
        """设置剪映项目路径"""
        config = self.get_project(project_dir)
        if config:
            config.jianying_project_path = jianying_path
            config.jianying_created_at = datetime.now().isoformat()
            config.status = ProjectStatus.EDIT_DONE
            config.save()

    def get_project_summary(self, project_dir: str) -> dict:
        """获取项目摘要"""
        config = self.get_project(project_dir)
        if not config:
            return {}

        return {
            'product_name': config.product_name,
            'status': config.status,
            'created_at': config.created_at,
            'found_count': len(config.found_videos),
            'filtered_count': len(config.filtered_videos),
            'downloaded_count': len(config.downloaded_videos),
            'has_jianying': bool(config.jianying_project_path),
            'has_upload': bool(config.douyin_video_id)
        }

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()


def test_project_manager():
    """测试项目管理器"""
    import tempfile

    # 使用临时目录测试
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ProjectManager(tmpdir)

        # 创建项目
        config = manager.create_project(
            product_name="测试产品",
            product_data={
                'commission_rate': '20%',
                'price': '99.00',
                'monthly_sales': '1000'
            },
            filter_settings={
                'min_duration': 15,
                'max_duration': 60,
                'min_likes': 1000
            }
        )

        print(f"创建项目: {config.project_id}")
        print(f"项目目录: {config.project_dir}")

        # 添加视频
        videos = [
            VideoItem(
                aweme_id="123456",
                url="https://www.douyin.com/video/123456",
                author="测试作者",
                duration=30,
                digg_count=5000
            ),
            VideoItem(
                aweme_id="789012",
                url="https://www.douyin.com/video/789012",
                author="测试作者2",
                duration=45,
                digg_count=8000
            )
        ]

        manager.add_found_videos(config.project_dir, videos)
        manager.add_filtered_videos(config.project_dir, videos)

        # 更新视频状态
        manager.update_video_status(
            config.project_dir,
            "123456",
            VideoStatus.DOWNLOADED,
            local_path="/path/to/video.mp4"
        )

        # 获取项目摘要
        summary = manager.get_project_summary(config.project_dir)
        print(f"项目摘要: {summary}")

        # 列出所有项目
        projects = manager.list_projects()
        print(f"项目数量: {len(projects)}")

        # 获取未完成项目
        incomplete = manager.get_incomplete_projects()
        print(f"未完成项目: {len(incomplete)}")


if __name__ == '__main__':
    test_project_manager()
