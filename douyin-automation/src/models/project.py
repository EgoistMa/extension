"""项目数据模型 - 管理整个工作流的状态"""

import json
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

from .product import Product
from .video import Video, ExportedVideo


class ProjectStatus(Enum):
    """项目状态枚举"""

    # 初始状态
    PENDING = "pending"

    # 产品阶段
    PRODUCT_SEARCHING = "product_searching"
    PRODUCT_FOUND = "product_found"
    MATERIAL_DOWNLOADING = "material_downloading"
    MATERIAL_DOWNLOADED = "material_downloaded"

    # 视频搜索阶段
    VIDEO_SEARCHING = "video_searching"
    VIDEO_FILTERED = "video_filtered"
    VIDEO_DOWNLOADING = "video_downloading"
    VIDEO_DOWNLOADED = "video_downloaded"

    # 剪辑阶段
    JIANYING_GENERATING = "jianying_generating"
    JIANYING_GENERATED = "jianying_generated"
    EXPORTING = "exporting"
    EXPORTED = "exported"

    # 上传阶段
    UPLOADING = "uploading"
    PUBLISHED = "published"

    # 终止状态
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProjectLog:
    """项目日志条目"""
    timestamp: str
    level: str  # info, warning, error
    message: str
    step: str = ""  # 对应的步骤

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Project:
    """项目 - 管理从选品到上传的完整流程

    每个Project对应一个产品的完整处理流程
    """

    # 基础信息
    project_id: str                                 # 项目ID
    name: str                                       # 项目名称
    account_id: str                                 # 关联的账户ID

    # 状态管理
    status: str = ProjectStatus.PENDING.value       # 当前状态
    current_step: str = ""                          # 当前步骤描述
    progress: float = 0.0                           # 进度 (0-100)

    # 产品信息
    product: Optional[Dict[str, Any]] = None        # Product数据

    # 搜索结果
    search_results_count: int = 0                   # 搜索结果总数
    filtered_results_count: int = 0                 # 筛选后数量
    downloaded_videos_count: int = 0                # 已下载数量

    # 视频列表
    videos: List[Dict[str, Any]] = field(default_factory=list)  # Video数据列表

    # 剪映项目
    jianying_draft_path: str = ""                   # 剪映草稿路径
    jianying_draft_name: str = ""                   # 剪映草稿名称

    # 导出信息
    exported_video: Optional[Dict[str, Any]] = None  # ExportedVideo数据

    # 日志
    logs: List[Dict[str, Any]] = field(default_factory=list)

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str = ""

    # 错误信息
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3

    # 项目目录
    project_dir: str = ""                           # 项目文件目录

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """从字典创建"""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def save(self, path: Optional[Path] = None) -> None:
        """保存到JSON文件"""
        if path is None:
            if self.project_dir:
                path = Path(self.project_dir) / "project.json"
            else:
                raise ValueError("未指定保存路径")

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'Project':
        """从JSON文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def update_status(self, status: ProjectStatus, step: str = "") -> None:
        """更新项目状态"""
        self.status = status.value
        self.current_step = step
        self.updated_at = datetime.now().isoformat()

        # 更新进度
        progress_map = {
            ProjectStatus.PENDING: 0,
            ProjectStatus.PRODUCT_SEARCHING: 5,
            ProjectStatus.PRODUCT_FOUND: 10,
            ProjectStatus.MATERIAL_DOWNLOADING: 15,
            ProjectStatus.MATERIAL_DOWNLOADED: 25,
            ProjectStatus.VIDEO_SEARCHING: 30,
            ProjectStatus.VIDEO_FILTERED: 40,
            ProjectStatus.VIDEO_DOWNLOADING: 50,
            ProjectStatus.VIDEO_DOWNLOADED: 60,
            ProjectStatus.JIANYING_GENERATING: 70,
            ProjectStatus.JIANYING_GENERATED: 80,
            ProjectStatus.EXPORTING: 85,
            ProjectStatus.EXPORTED: 90,
            ProjectStatus.UPLOADING: 95,
            ProjectStatus.PUBLISHED: 100,
            ProjectStatus.COMPLETED: 100,
        }
        self.progress = progress_map.get(status, self.progress)

    def add_log(self, message: str, level: str = "info", step: str = "") -> None:
        """添加日志"""
        log = ProjectLog(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            step=step or self.current_step
        )
        self.logs.append(log.to_dict())

    def set_product(self, product: Product) -> None:
        """设置产品信息"""
        self.product = product.to_dict()
        self.name = product.title[:50]  # 使用产品标题作为项目名

    def get_product(self) -> Optional[Product]:
        """获取产品信息"""
        if self.product:
            return Product.from_dict(self.product)
        return None

    def add_video(self, video: Video) -> None:
        """添加视频"""
        self.videos.append(video.to_dict())

    def get_videos(self) -> List[Video]:
        """获取所有视频"""
        return [Video.from_dict(v) for v in self.videos]

    def set_exported_video(self, video: ExportedVideo) -> None:
        """设置导出的视频"""
        self.exported_video = video.to_dict()

    def get_exported_video(self) -> Optional[ExportedVideo]:
        """获取导出的视频"""
        if self.exported_video:
            return ExportedVideo.from_dict(self.exported_video)
        return None

    def mark_failed(self, error: str) -> None:
        """标记为失败"""
        self.status = ProjectStatus.FAILED.value
        self.error_message = error
        self.updated_at = datetime.now().isoformat()
        self.add_log(f"项目失败: {error}", level="error")

    def mark_completed(self) -> None:
        """标记为完成"""
        self.status = ProjectStatus.COMPLETED.value
        self.completed_at = datetime.now().isoformat()
        self.updated_at = self.completed_at
        self.progress = 100
        self.add_log("项目完成")

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """增加重试次数"""
        self.retry_count += 1

    @property
    def is_finished(self) -> bool:
        """是否已结束"""
        return self.status in [
            ProjectStatus.COMPLETED.value,
            ProjectStatus.FAILED.value,
            ProjectStatus.CANCELLED.value
        ]

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return not self.is_finished and self.status != ProjectStatus.PENDING.value
