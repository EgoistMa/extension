"""断点恢复模块"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from models.project import Project, ProjectStatus


class Checkpoint:
    """断点管理器

    支持在任意步骤保存和恢复项目状态
    """

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """初始化断点管理器

        Args:
            checkpoint_dir: 断点文件目录
        """
        if checkpoint_dir is None:
            checkpoint_dir = Path(__file__).parent.parent.parent / "data" / "checkpoints"
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, project: Project) -> str:
        """保存项目断点

        Args:
            project: 项目对象

        Returns:
            断点文件路径
        """
        checkpoint_file = self.checkpoint_dir / f"{project.project_id}.json"

        # 添加断点元数据
        checkpoint_data = {
            "project": project.to_dict(),
            "saved_at": datetime.now().isoformat(),
            "status": project.status,
            "progress": project.progress,
        }

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

        return str(checkpoint_file)

    def load(self, project_id: str) -> Optional[Project]:
        """加载项目断点

        Args:
            project_id: 项目ID

        Returns:
            项目对象，不存在返回None
        """
        checkpoint_file = self.checkpoint_dir / f"{project_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            project_data = data.get("project", {})
            return Project.from_dict(project_data)
        except Exception:
            return None

    def delete(self, project_id: str) -> bool:
        """删除断点

        Args:
            project_id: 项目ID

        Returns:
            是否删除成功
        """
        checkpoint_file = self.checkpoint_dir / f"{project_id}.json"

        if checkpoint_file.exists():
            checkpoint_file.unlink()
            return True
        return False

    def list_checkpoints(self) -> list:
        """列出所有断点

        Returns:
            断点信息列表
        """
        checkpoints = []

        for file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                project_data = data.get("project", {})
                checkpoints.append({
                    "project_id": project_data.get("project_id"),
                    "name": project_data.get("name"),
                    "status": data.get("status"),
                    "progress": data.get("progress"),
                    "saved_at": data.get("saved_at"),
                    "file": str(file)
                })
            except Exception:
                continue

        # 按保存时间排序
        checkpoints.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return checkpoints

    def get_resumable_projects(self) -> list:
        """获取可恢复的项目列表

        Returns:
            可恢复的项目列表
        """
        checkpoints = self.list_checkpoints()

        resumable = []
        for cp in checkpoints:
            status = cp.get("status")
            # 只返回未完成的项目
            if status not in [
                ProjectStatus.COMPLETED.value,
                ProjectStatus.CANCELLED.value
            ]:
                resumable.append(cp)

        return resumable

    def can_resume(self, project_id: str) -> bool:
        """检查项目是否可以恢复

        Args:
            project_id: 项目ID

        Returns:
            是否可以恢复
        """
        project = self.load(project_id)
        if project is None:
            return False

        return not project.is_finished

    def get_resume_step(self, project: Project) -> str:
        """获取恢复步骤

        Args:
            project: 项目对象

        Returns:
            应该恢复的步骤名称
        """
        status = project.status

        # 根据状态确定恢复步骤
        status_to_step = {
            ProjectStatus.PENDING.value: "product_search",
            ProjectStatus.PRODUCT_SEARCHING.value: "product_search",
            ProjectStatus.PRODUCT_FOUND.value: "material_download",
            ProjectStatus.MATERIAL_DOWNLOADING.value: "material_download",
            ProjectStatus.MATERIAL_DOWNLOADED.value: "video_search",
            ProjectStatus.VIDEO_SEARCHING.value: "video_search",
            ProjectStatus.VIDEO_FILTERED.value: "video_download",
            ProjectStatus.VIDEO_DOWNLOADING.value: "video_download",
            ProjectStatus.VIDEO_DOWNLOADED.value: "jianying_generate",
            ProjectStatus.JIANYING_GENERATING.value: "jianying_generate",
            ProjectStatus.JIANYING_GENERATED.value: "jianying_export",
            ProjectStatus.EXPORTING.value: "jianying_export",
            ProjectStatus.EXPORTED.value: "douyin_upload",
            ProjectStatus.UPLOADING.value: "douyin_upload",
            ProjectStatus.PUBLISHED.value: "complete",
            ProjectStatus.FAILED.value: "retry",
        }

        return status_to_step.get(status, "unknown")

    def auto_save(self, project: Project) -> None:
        """自动保存（在关键步骤后调用）

        Args:
            project: 项目对象
        """
        # 只在特定状态后保存
        save_statuses = [
            ProjectStatus.PRODUCT_FOUND,
            ProjectStatus.MATERIAL_DOWNLOADED,
            ProjectStatus.VIDEO_FILTERED,
            ProjectStatus.VIDEO_DOWNLOADED,
            ProjectStatus.JIANYING_GENERATED,
            ProjectStatus.EXPORTED,
            ProjectStatus.PUBLISHED,
            ProjectStatus.FAILED,
        ]

        if ProjectStatus(project.status) in save_statuses:
            self.save(project)
