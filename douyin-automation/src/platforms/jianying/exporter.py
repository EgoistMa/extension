"""剪映自动导出模块

使用pyJianYingDraft和uiautomation控制剪映导出视频
"""

import os
import time
import json
import subprocess
from pathlib import Path
from typing import Optional, Callable, Literal

from core.config import Config
from models.video import ExportedVideo


class JianyingExporter:
    """剪映自动导出器"""

    def __init__(self, config: Optional[Config] = None):
        """初始化导出器

        Args:
            config: 配置对象
        """
        self.config = config or Config()
        self.jianying_app_path = self.config.get('jianying.app_path', '')
        self.export_timeout = self.config.get('jianying.export_timeout', 1200)

    def export_draft(
        self,
        draft_path: str,
        output_path: Optional[str] = None,
        resolution: str = "1080P",
        framerate: str = "30fps",
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> Optional[ExportedVideo]:
        """导出剪映草稿

        Args:
            draft_path: 草稿目录路径
            output_path: 输出文件路径
            resolution: 分辨率
            framerate: 帧率
            on_log: 日志回调
            on_progress: 进度回调

        Returns:
            ExportedVideo对象，失败返回None
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        draft_path = Path(draft_path)
        if not draft_path.exists():
            log(f"草稿路径不存在: {draft_path}")
            return None

        # 获取草稿名称
        draft_name = self._get_draft_name(draft_path)
        if not draft_name:
            log("无法获取草稿名称")
            return None

        log(f"开始导出: {draft_name}")

        if on_progress:
            on_progress("启动剪映", 1, 5)

        # 确保剪映已关闭
        self._kill_jianying()
        time.sleep(2)

        # 启动剪映
        if not self._start_jianying():
            log("启动剪映失败")
            return None

        if on_progress:
            on_progress("等待剪映加载", 2, 5)

        # 等待剪映窗口
        if not self._wait_for_jianying_window():
            log("等待剪映窗口超时")
            return None

        log("剪映已启动")

        # 尝试使用pyJianYingDraft的控制器
        try:
            from pyJianYingDraft import JianyingController, ExportResolution, ExportFramerate

            if on_progress:
                on_progress("导出视频", 3, 5)

            # 获取分辨率和帧率枚举
            res_map = {
                "8K": ExportResolution.RES_8K,
                "4K": ExportResolution.RES_4K,
                "2K": ExportResolution.RES_2K,
                "1080P": ExportResolution.RES_1080P,
                "720P": ExportResolution.RES_720P,
                "480P": ExportResolution.RES_480P,
            }
            fps_map = {
                "24fps": ExportFramerate.FR_24,
                "25fps": ExportFramerate.FR_25,
                "30fps": ExportFramerate.FR_30,
                "50fps": ExportFramerate.FR_50,
                "60fps": ExportFramerate.FR_60,
            }

            res = res_map.get(resolution)
            fps = fps_map.get(framerate)

            # 创建控制器并导出
            controller = JianyingController()
            controller.export_draft(
                draft_name=draft_name,
                output_path=output_path,
                resolution=res,
                framerate=fps,
                timeout=self.export_timeout
            )

            if on_progress:
                on_progress("导出完成", 5, 5)

            log(f"导出完成: {output_path}")

            # 创建ExportedVideo对象
            return ExportedVideo(
                video_id=draft_name,
                local_path=output_path or ""
            )

        except ImportError:
            log("pyJianYingDraft未安装，请安装: pip install pyJianYingDraft")
            return None
        except Exception as e:
            log(f"导出失败: {e}")
            return None

    def _get_draft_name(self, draft_path: Path) -> str:
        """获取草稿名称"""
        meta_file = draft_path / "draft_meta_info.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                return meta.get('draft_name', '')
            except Exception:
                pass
        return draft_path.name

    def _kill_jianying(self) -> None:
        """关闭剪映进程"""
        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/IM', 'JianyingPro.exe'],
                             capture_output=True, timeout=10)
        except Exception:
            pass

    def _start_jianying(self) -> bool:
        """启动剪映"""
        # 使用配置的路径
        if self.jianying_app_path and Path(self.jianying_app_path).exists():
            try:
                subprocess.Popen([self.jianying_app_path])
                return True
            except Exception:
                pass

        # 尝试常见路径
        possible_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / "JianyingPro" / "Apps" / "JianyingPro.exe",
            Path("C:/Program Files/JianyingPro/JianyingPro.exe"),
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    subprocess.Popen([str(path)])
                    return True
                except Exception:
                    continue

        return False

    def _wait_for_jianying_window(self, timeout: int = 60) -> bool:
        """等待剪映窗口出现"""
        try:
            import uiautomation as uia

            start_time = time.time()
            while time.time() - start_time < timeout:
                # 查找剪映窗口
                window = uia.WindowControl(
                    searchDepth=1,
                    Name="剪映专业版"
                )
                if window.Exists(1):
                    return True
                time.sleep(2)

            return False
        except ImportError:
            # 如果没有uiautomation，等待固定时间
            time.sleep(15)
            return True
        except Exception:
            time.sleep(15)
            return True

    def batch_export(
        self,
        draft_paths: list,
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> list:
        """批量导出草稿

        Args:
            draft_paths: 草稿路径列表
            output_dir: 输出目录
            on_log: 日志回调
            on_progress: 进度回调

        Returns:
            ExportedVideo对象列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        total = len(draft_paths)

        for i, draft_path in enumerate(draft_paths):
            log(f"\n[{i+1}/{total}] 导出: {draft_path}")

            if on_progress:
                on_progress(f"导出 {i+1}/{total}", i+1, total)

            draft_name = self._get_draft_name(Path(draft_path))
            output_path = str(output_dir / f"{draft_name}.mp4")

            video = self.export_draft(draft_path, output_path, on_log=log)
            if video:
                exported.append(video)

        log(f"\n导出完成: {len(exported)}/{total}")
        return exported
