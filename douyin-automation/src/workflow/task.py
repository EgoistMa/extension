"""任务定义"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Any, Dict


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class Task:
    """工作流任务"""

    # 基础信息
    task_id: str
    name: str
    description: str = ""

    # 状态
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0  # 0-100
    message: str = ""

    # 时间
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = ""
    completed_at: str = ""

    # 错误信息
    error: str = ""
    retry_count: int = 0
    max_retries: int = 3

    # 输入输出
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """从字典创建"""
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        return cls(**data)

    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now().isoformat()
        self.message = "任务开始"

    def complete(self, output: Optional[Dict] = None) -> None:
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.progress = 100.0
        self.message = "任务完成"
        if output:
            self.output_data = output

    def fail(self, error: str) -> None:
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.message = f"任务失败: {error}"

    def cancel(self) -> None:
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.message = "任务已取消"

    def pause(self) -> None:
        """暂停任务"""
        self.status = TaskStatus.PAUSED
        self.message = "任务已暂停"

    def resume(self) -> None:
        """恢复任务"""
        self.status = TaskStatus.RUNNING
        self.message = "任务已恢复"

    def update_progress(self, progress: float, message: str = "") -> None:
        """更新进度"""
        self.progress = min(100.0, max(0.0, progress))
        if message:
            self.message = message

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """增加重试次数"""
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.error = ""
        self.message = f"重试 {self.retry_count}/{self.max_retries}"

    @property
    def is_finished(self) -> bool:
        """是否已结束"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        ]

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == TaskStatus.RUNNING

    @property
    def duration_seconds(self) -> float:
        """任务持续时间(秒)"""
        if not self.started_at:
            return 0

        start = datetime.fromisoformat(self.started_at)

        if self.completed_at:
            end = datetime.fromisoformat(self.completed_at)
        else:
            end = datetime.now()

        return (end - start).total_seconds()
