#!/usr/bin/env python3
"""
百应视频素材下载器
接收选品数据，异步下载抖音视频素材
"""

import sys
import os
import json
import asyncio
import threading
import queue
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

# GUI
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QTextEdit, QGroupBox, QFormLayout, QTabWidget, QFileDialog,
    QMessageBox, QSplitter, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

# HTTP Server
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加父目录到路径以导入downloader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from douyin_downloader.douyin_search_downloader import DouyinSearchDownloader, VideoInfo
except ImportError:
    # 如果导入失败，定义一个简单的类
    class VideoInfo:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    DouyinSearchDownloader = None

try:
    from jianying_generator import JianyingGenerator
    print("[启动] JianyingGenerator 模块加载成功")
except ImportError as e:
    print(f"[启动] JianyingGenerator 模块加载失败: {e}")
    JianyingGenerator = None

# 剪映自动导出控制器
try:
    import pyJianYingDraft as pjd
    from pyJianYingDraft import JianyingController, ExportResolution, ExportFramerate
    print("[启动] pyJianYingDraft 模块加载成功（支持自动导出）")
    HAS_JIANYING_CONTROLLER = True
except ImportError as e:
    print(f"[启动] pyJianYingDraft 模块加载失败: {e}")
    HAS_JIANYING_CONTROLLER = False
    JianyingController = None
    # 尝试从当前目录导入
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "jianying_generator",
            Path(__file__).parent / "jianying_generator.py"
        )
        jianying_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(jianying_module)
        JianyingGenerator = jianying_module.JianyingGenerator
        print("[启动] JianyingGenerator 模块通过备用方式加载成功")
    except Exception as e2:
        print(f"[启动] JianyingGenerator 模块加载彻底失败: {e2}")
        JianyingGenerator = None

try:
    from project_manager import ProjectManager, ProjectConfig, ProjectStatus, VideoStatus, VideoItem
    print("[启动] ProjectManager 模块加载成功")
except ImportError as e:
    print(f"[启动] ProjectManager 模块加载失败: {e}")
    ProjectManager = None
    ProjectConfig = None
    ProjectStatus = None
    VideoStatus = None
    VideoItem = None


class ProductData:
    """产品数据"""
    def __init__(self, data: dict):
        self.name = data.get('name', '')
        self.commission_rate = data.get('commission_rate', '')
        self.commission_amount = data.get('commission_amount', '')
        self.price = data.get('price', '')
        self.monthly_sales = data.get('monthly_sales', '')
        self.shop_score = data.get('shop_score', '')
        self.total_score = data.get('totalScore', 0)
        self.status = 'pending'  # pending, downloading, completed, failed
        self.videos_downloaded = 0
        self.retry_count = 0  # 重试次数
        self.project_dir = data.get('project_dir', '')  # 项目目录
        self.project_config = None  # ProjectConfig 对象

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'commission_rate': self.commission_rate,
            'commission_amount': self.commission_amount,
            'price': self.price,
            'monthly_sales': self.monthly_sales,
            'shop_score': self.shop_score,
            'totalScore': self.total_score,
        }


class DownloadWorker(QThread):
    """下载工作线程"""
    progress = pyqtSignal(str, str, int)  # product_name, status, video_count
    log = pyqtSignal(str)
    finished_product = pyqtSignal(str)

    def __init__(self, product: ProductData, settings: dict):
        super().__init__()
        self.product = product
        self.settings = settings
        self.is_running = True

    def run(self):
        """执行下载任务"""
        product_name = self.product.name
        self.progress.emit(product_name, 'downloading', 0)
        self.log.emit(f"[开始] 搜索产品: {product_name}")

        # 初始化项目管理器
        project_manager = None
        project_config = None
        if ProjectManager:
            output_dir = Path(self.settings.get('output_dir', './downloads'))
            project_manager = ProjectManager(str(output_dir))

            # 如果是从历史项目继续，使用已有配置
            if self.product.project_dir and Path(self.product.project_dir).exists():
                project_config = ProjectConfig.load(self.product.project_dir)
                if project_config:
                    self.log.emit(f"[项目] 继续历史项目: {project_config.project_id}")

            # 否则创建新项目
            if not project_config:
                project_config = project_manager.create_project(
                    product_name=product_name,
                    product_data=self.product.to_dict(),
                    filter_settings=self.settings
                )
                self.product.project_dir = project_config.project_dir
                self.log.emit(f"[项目] 创建新项目: {project_config.project_id}")

            project_config.status = ProjectStatus.SEARCHING
            project_config.save()

        try:
            if DouyinSearchDownloader is None:
                self.log.emit(f"[错误] 未找到 DouyinSearchDownloader 模块")
                self.progress.emit(product_name, 'failed', 0)
                if project_config:
                    project_config.status = ProjectStatus.FAILED
                    project_config.error_message = "未找到 DouyinSearchDownloader 模块"
                    project_config.save()
                return

            # 创建下载器 - 建议关闭无头模式以便处理验证码
            headless = self.settings.get('headless', True)
            if headless:
                self.log.emit(f"[提示] 无头模式已开启，如遇验证码请在设置中关闭无头模式")

            downloader = DouyinSearchDownloader(
                headless=headless,
                debug=self.settings.get('debug', False)
            )

            # 构建搜索URL
            search_keyword = product_name[:20]  # 取前20个字符作为搜索关键词
            search_url = f"https://www.douyin.com/search/{quote(search_keyword)}?type=video"

            self.log.emit(f"[搜索] URL: {search_url}")
            self.log.emit(f"[提示] 如出现验证码，请在浏览器窗口中完成验证（最多等待120秒）")

            # 搜索视频
            videos = downloader.search_videos(
                search_url,
                scroll_times=self.settings.get('scroll_times', 3)
            )

            self.log.emit(f"[结果] 找到 {len(videos)} 个视频")

            # 保存找到的视频到项目配置
            if project_config and videos:
                found_videos = []
                for v in videos:
                    found_videos.append({
                        'aweme_id': v.aweme_id,
                        'url': f"https://www.douyin.com/video/{v.aweme_id}",
                        'video_url': getattr(v, 'video_url', ''),
                        'author': v.author,
                        'title': getattr(v, 'title', ''),
                        'duration': v.duration,
                        'digg_count': v.digg_count,
                        'comment_count': getattr(v, 'comment_count', 0),
                        'share_count': getattr(v, 'share_count', 0),
                        'status': 'found'
                    })
                project_config.found_videos = found_videos
                project_config.save()

            # 打印所有找到的视频详情
            if videos:
                self.log.emit(f"\n{'─'*70}")
                self.log.emit(f"{'序号':^4} | {'视频URL':<40} | {'作者':<10} | {'点赞':>8} | {'时长':>5}")
                self.log.emit(f"{'─'*70}")
                for i, v in enumerate(videos[:20], 1):  # 最多显示20个
                    video_url = f"https://www.douyin.com/video/{v.aweme_id}"
                    author = (v.author[:8] + '..') if len(v.author) > 10 else v.author
                    likes = self._format_count(v.digg_count)
                    duration = f"{int(v.duration)}s" if v.duration > 0 else "-"
                    self.log.emit(f"{i:^4} | {video_url:<40} | {author:<10} | {likes:>8} | {duration:>5}")
                if len(videos) > 20:
                    self.log.emit(f"     ... 还有 {len(videos) - 20} 个视频未显示")
                self.log.emit(f"{'─'*70}\n")

            if not videos:
                self.progress.emit(product_name, 'failed', 0)
                self.log.emit(f"[失败] 未找到相关视频")
                if project_config:
                    project_config.status = ProjectStatus.FAILED
                    project_config.error_message = "未找到相关视频"
                    project_config.save()
                downloader.close()
                return

            # 筛选视频
            min_likes = self.settings.get('min_likes', 0)
            if min_likes > 0:
                videos = [v for v in videos if v.digg_count >= min_likes]
                self.log.emit(f"[筛选] 点赞数 >= {min_likes}: {len(videos)} 个视频")

            filtered = downloader.filter_videos(
                videos,
                min_duration=self.settings.get('min_duration', 15),
                max_duration=self.settings.get('max_duration', 30),
                top_n=self.settings.get('download_count', 3),
                sort_by=self.settings.get('sort_by', 'digg_time')
            )

            self.log.emit(f"[筛选] 筛选后 {len(filtered)} 个视频")

            # 保存筛选后的视频到项目配置
            if project_config and filtered:
                filtered_videos = []
                for v in filtered:
                    filtered_videos.append({
                        'aweme_id': v.aweme_id,
                        'url': f"https://www.douyin.com/video/{v.aweme_id}",
                        'video_url': getattr(v, 'video_url', ''),
                        'author': v.author,
                        'title': getattr(v, 'title', ''),
                        'duration': v.duration,
                        'digg_count': v.digg_count,
                        'comment_count': getattr(v, 'comment_count', 0),
                        'share_count': getattr(v, 'share_count', 0),
                        'status': 'filtered'
                    })
                project_config.filtered_videos = filtered_videos
                project_config.status = ProjectStatus.DOWNLOADING
                project_config.save()

            # 打印筛选后的视频
            if filtered:
                self.log.emit(f"\n[即将下载的视频]")
                for i, v in enumerate(filtered, 1):
                    video_url = f"https://www.douyin.com/video/{v.aweme_id}"
                    likes = self._format_count(v.digg_count)
                    self.log.emit(f"  {i}. {video_url} | 点赞:{likes} | 时长:{int(v.duration)}s")

            if not filtered:
                self.progress.emit(product_name, 'failed', 0)
                self.log.emit(f"[失败] 没有符合条件的视频")
                if project_config:
                    project_config.status = ProjectStatus.FAILED
                    project_config.error_message = "没有符合条件的视频"
                    project_config.save()
                downloader.close()
                return

            # 使用项目目录或创建输出目录
            if project_config:
                product_dir = Path(project_config.project_dir)
            else:
                output_dir = Path(self.settings.get('output_dir', './downloads'))
                base_name = self._safe_filename(product_name[:30])
                timestamp = datetime.now().strftime('%m%d_%H%M%S')
                if self.product.retry_count > 0:
                    product_dir = output_dir / f"{base_name}_{timestamp}_retry{self.product.retry_count}"
                    self.log.emit(f"[重试] 创建新文件夹: {product_dir.name}")
                else:
                    product_dir = output_dir / f"{base_name}_{timestamp}"

            product_dir.mkdir(parents=True, exist_ok=True)
            self.log.emit(f"[下载] 保存目录: {product_dir.name}")

            # 下载视频
            downloaded = 0
            for i, video in enumerate(filtered):
                if not self.is_running:
                    break

                self.log.emit(f"[下载] ({i+1}/{len(filtered)}) 视频ID: {video.aweme_id}")

                # 更新视频状态为下载中
                if project_config:
                    for fv in project_config.filtered_videos:
                        if fv['aweme_id'] == video.aweme_id:
                            fv['status'] = 'downloading'
                    project_config.save()

                # 获取视频URL
                video_url = video.video_url
                if not video_url or 'douyin' not in video_url:
                    video_url = downloader.get_video_url(video.aweme_id)

                if video_url:
                    filename = f"{video.aweme_id}_{video.duration:.0f}s_{video.digg_count}.mp4"
                    filepath = product_dir / filename

                    if downloader.download_video(video_url, str(filepath)):
                        downloaded += 1
                        self.progress.emit(product_name, 'downloading', downloaded)
                        self.log.emit(f"[成功] 已下载: {filename}")

                        # 更新视频状态为已下载
                        if project_config:
                            for fv in project_config.filtered_videos:
                                if fv['aweme_id'] == video.aweme_id:
                                    fv['status'] = 'downloaded'
                                    fv['local_path'] = str(filepath)
                                    fv['downloaded_at'] = datetime.now().isoformat()
                                    # 添加到已下载列表
                                    if fv not in project_config.downloaded_videos:
                                        project_config.downloaded_videos.append(fv.copy())
                            project_config.save()
                    else:
                        self.log.emit(f"[失败] 下载失败: {video.aweme_id}")
                        if project_config:
                            for fv in project_config.filtered_videos:
                                if fv['aweme_id'] == video.aweme_id:
                                    fv['status'] = 'failed'
                                    fv['error_message'] = '下载失败'
                            project_config.save()
                else:
                    self.log.emit(f"[失败] 无法获取视频URL: {video.aweme_id}")
                    if project_config:
                        for fv in project_config.filtered_videos:
                            if fv['aweme_id'] == video.aweme_id:
                                fv['status'] = 'failed'
                                fv['error_message'] = '无法获取视频URL'
                        project_config.save()

            downloader.close()

            if downloaded > 0:
                self.progress.emit(product_name, 'completed', downloaded)
                self.log.emit(f"[完成] {product_name}: 成功下载 {downloaded} 个视频")

                # 更新项目状态为下载完成
                if project_config:
                    project_config.status = ProjectStatus.DOWNLOAD_DONE
                    project_config.save()

                # 生成剪映项目
                auto_jianying = self.settings.get('auto_jianying', False)
                self.log.emit(f"[调试] auto_jianying={auto_jianying}, JianyingGenerator={'可用' if JianyingGenerator else '不可用'}")
                if auto_jianying and JianyingGenerator:
                    self.log.emit(f"[剪映] 开始生成剪映项目...")
                    if project_config:
                        project_config.status = ProjectStatus.EDITING
                        project_config.save()
                    jianying_path = self._generate_jianying_project(product_dir, product_name)
                    if jianying_path and project_config:
                        project_config.jianying_project_path = jianying_path
                        project_config.jianying_created_at = datetime.now().isoformat()
                        project_config.status = ProjectStatus.EDIT_DONE
                        project_config.save()
                elif auto_jianying and not JianyingGenerator:
                    self.log.emit(f"[剪映] 自动剪映已启用，但 JianyingGenerator 模块未加载")
            else:
                self.progress.emit(product_name, 'failed', 0)
                self.log.emit(f"[失败] {product_name}: 没有成功下载任何视频")
                if project_config:
                    project_config.status = ProjectStatus.FAILED
                    project_config.error_message = "没有成功下载任何视频"
                    project_config.save()

        except Exception as e:
            error_msg = str(e).lower()
            # 检测连接断开相关的错误
            connection_errors = [
                'disconnected', 'connection', 'no browser',
                'page crashed', 'target closed', 'session closed',
                'not connected', 'browser closed', 'lost connection',
                'websocket', 'timeout', 'timed out'
            ]
            is_connection_error = any(err in error_msg for err in connection_errors)

            if is_connection_error:
                self.log.emit(f"[连接断开] {product_name}: 浏览器连接已断开")
            else:
                self.log.emit(f"[错误] {product_name}: {str(e)}")

            self.progress.emit(product_name, 'failed', 0)

            # 尝试关闭下载器
            try:
                if 'downloader' in locals():
                    downloader.close()
            except Exception:
                pass

        self.finished_product.emit(product_name)

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def _format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        elif count >= 1000:
            return f"{count/1000:.1f}k"
        else:
            return str(count)

    def _generate_jianying_project(self, video_dir: Path, product_name: str) -> str:
        """生成剪映项目，返回项目路径"""
        try:
            template_path = self.settings.get('jianying_template', '')
            self.log.emit(f"[剪映] 模板路径: {template_path}")

            if not template_path:
                self.log.emit(f"[剪映] 未设置模板路径，跳过生成")
                return None

            if not Path(template_path).exists():
                self.log.emit(f"[剪映] 模板路径不存在: {template_path}")
                return None

            # 获取下载的视频文件
            self.log.emit(f"[剪映] 视频目录: {video_dir}")
            video_files = sorted(video_dir.glob("*.mp4"))
            self.log.emit(f"[剪映] 找到 {len(video_files)} 个 MP4 文件")

            if not video_files:
                self.log.emit(f"[剪映] 未找到视频文件，跳过生成")
                return None

            self.log.emit(f"[剪映] 正在生成项目，使用 {len(video_files)} 个视频...")

            # 获取剪映草稿输出目录
            draft_output_dir = self.settings.get('jianying_draft_dir', '')
            if draft_output_dir:
                self.log.emit(f"[剪映] 草稿输出目录: {draft_output_dir}")

            # 创建生成器
            generator = JianyingGenerator(template_path, output_base_dir=draft_output_dir if draft_output_dir else None)
            self.log.emit(f"[剪映] 生成器创建成功")

            # 生成项目名称（包含时间戳避免同名冲突）
            safe_name = self._safe_filename(product_name[:20])
            timestamp = datetime.now().strftime('%m%d_%H%M%S')
            project_name = f"{safe_name}_{timestamp}"
            self.log.emit(f"[剪映] 项目名称: {project_name}")

            # 生成项目
            project_path = generator.generate_project(
                video_files=[str(f) for f in video_files],
                project_name=project_name,
                auto_open=False
            )

            self.log.emit(f"[剪映] 项目已生成: {project_path}")
            return project_path

        except Exception as e:
            import traceback
            self.log.emit(f"[剪映] 生成项目失败: {e}")
            self.log.emit(f"[剪映] 详细错误: {traceback.format_exc()}")
            return None

    def stop(self):
        self.is_running = False


class ExportWorker(QThread):
    """剪映导出工作线程"""
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)  # status message

    def __init__(self, project, settings: dict):
        super().__init__()
        self.project = project
        self.settings = settings
        self.is_running = True

    def run(self):
        """执行导出任务"""
        import time as time_module
        import subprocess

        try:
            # 获取剪映项目路径
            jianying_path = Path(self.project.jianying_project_path)

            # 从 draft_meta_info.json 读取真实的草稿名称
            meta_file = jianying_path / "draft_meta_info.json"
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    draft_name = meta.get('draft_name', jianying_path.name)
                    self.log.emit(f"[导出] 从 draft_meta_info.json 读取草稿名称: {draft_name}")
                except Exception as e:
                    self.log.emit(f"[导出] 读取 draft_meta_info.json 失败: {e}，使用文件夹名")
                    draft_name = jianying_path.name
            else:
                draft_name = jianying_path.name
                self.log.emit(f"[导出] draft_meta_info.json 不存在，使用文件夹名: {draft_name}")

            # 导出路径
            export_dir = Path(self.project.project_dir)
            invalid_chars = '<>:"/\\|?*'
            safe_name = self.project.product_name
            for char in invalid_chars:
                safe_name = safe_name.replace(char, '_')
            export_path = export_dir / f"{safe_name.strip()}_导出.mp4"

            self.log.emit(f"[导出] 开始自动导出剪映项目: {draft_name}")
            self.log.emit(f"[导出] 剪映草稿路径: {jianying_path}")
            self.log.emit(f"[导出] 导出路径: {export_path}")

            # 检查剪映是否正在运行
            def is_jianying_running():
                try:
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq JianyingPro.exe'],
                        capture_output=True, text=True, timeout=5
                    )
                    return 'JianyingPro.exe' in result.stdout
                except Exception:
                    return False

            def kill_jianying():
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'JianyingPro.exe'],
                                  capture_output=True, timeout=10)
                    time_module.sleep(2)
                    return True
                except Exception:
                    return False

            # 如果剪映正在运行，先关闭它
            if is_jianying_running():
                self.log.emit("[导出] 检测到剪映正在运行，正在关闭...")
                self.progress.emit("正在关闭剪映...")
                if not kill_jianying():
                    self.finished.emit(False, "关闭剪映失败，请手动关闭后重试")
                    return
                self.log.emit("[导出] 剪映已关闭")
                time_module.sleep(2)

            # 启动剪映
            jianying_app_path = self.settings.get('jianying_app_path', '')
            if not jianying_app_path or not os.path.exists(jianying_app_path):
                self.finished.emit(False, "未找到剪映程序路径，请在设置中指定")
                return

            self.log.emit(f"[导出] 正在启动剪映: {jianying_app_path}")
            self.progress.emit("正在启动剪映...")
            subprocess.Popen([jianying_app_path], shell=True)

            # 等待剪映窗口出现
            try:
                import uiautomation as uia
            except ImportError:
                self.finished.emit(False, "uiautomation 未安装，无法自动检测剪映窗口")
                return

            self.log.emit("[导出] 等待剪映窗口出现（最长60秒）...")
            self.progress.emit("等待剪映启动...")

            start_time = time_module.time()
            window_found = False
            while time_module.time() - start_time < 60 and self.is_running:
                try:
                    window = uia.WindowControl(searchDepth=1, Name="剪映专业版")
                    if window.Exists(0.5):
                        if "HomePage".lower() in window.ClassName.lower() or "MainWindow".lower() in window.ClassName.lower():
                            self.log.emit("[导出] 检测到剪映窗口")
                            window_found = True
                            break
                except Exception:
                    pass
                time_module.sleep(1)
                elapsed = int(time_module.time() - start_time)
                if elapsed % 5 == 0:
                    self.log.emit(f"[导出] 等待剪映启动... ({elapsed}/60秒)")

            if not window_found:
                self.finished.emit(False, "等待剪映启动超时")
                return

            # 额外等待剪映加载草稿列表
            self.log.emit("[导出] 剪映窗口已出现，等待草稿列表加载（15秒）...")
            self.progress.emit("等待草稿列表加载...")
            time_module.sleep(15)

            if not self.is_running:
                self.finished.emit(False, "导出已取消")
                return

            self.log.emit(f"[导出] 开始自动导出草稿: {draft_name}")
            self.progress.emit("正在导出视频...")

            # 创建控制器并导出
            ctrl = JianyingController()

            # 尝试导出，如果失败则重试
            max_retries = 3
            last_error = None
            for attempt in range(max_retries):
                if not self.is_running:
                    self.finished.emit(False, "导出已取消")
                    return
                try:
                    ctrl.export_draft(
                        draft_name,
                        str(export_path),
                        resolution=ExportResolution.RES_1080P,
                        framerate=ExportFramerate.FR_30
                    )
                    # 成功
                    self.log.emit(f"[导出] 导出完成: {export_path}")
                    self.finished.emit(True, str(export_path))
                    return
                except Exception as e:
                    last_error = str(e)
                    if "未找到" in str(e) and attempt < max_retries - 1:
                        self.log.emit(f"[导出] 第 {attempt + 1} 次尝试失败，等待5秒后重试...")
                        time_module.sleep(5)
                        try:
                            ctrl.get_window()
                        except Exception:
                            pass
                    else:
                        break

            self.finished.emit(False, f"导出失败: {last_error}")

        except Exception as e:
            import traceback
            self.log.emit(f"[导出] 导出失败: {e}")
            self.log.emit(f"[导出] 详细错误: {traceback.format_exc()}")
            self.finished.emit(False, str(e))

    def stop(self):
        self.is_running = False


class ServerThread(QThread):
    """HTTP服务器线程"""
    product_received = pyqtSignal(dict)
    log = pyqtSignal(str)

    def __init__(self, port: int = 5000):
        super().__init__()
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/api/products', methods=['POST'])
        def receive_products():
            try:
                data = request.json
                self.log.emit(f"[服务器] 收到请求: {data.get('product_count', 0)} 个产品")
                self.product_received.emit(data)
                return jsonify({'success': True, 'message': '已接收产品列表'})
            except Exception as e:
                self.log.emit(f"[服务器错误] {str(e)}")
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({'status': 'running', 'port': self.port})

    def run(self):
        self.log.emit(f"[服务器] 启动在端口 {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, threaded=True, use_reloader=False)


class MainWindow(QMainWindow):
    """主窗口"""

    # 设置文件路径
    SETTINGS_FILE = Path(__file__).parent / "settings.json"

    # 默认设置
    DEFAULT_SETTINGS = {
        'port': 5000,
        'auto_download': True,
        'min_duration': 15,
        'max_duration': 60,
        'min_likes': 1000,
        'sort_by': 'digg_time',
        'download_count': 3,
        'scroll_times': 5,
        'output_dir': str(Path.home() / "Downloads" / "baiying_videos"),
        'headless': True,
        'debug': False,
        'auto_jianying': False,
        'jianying_template': '',
        'jianying_draft_dir': str(Path(os.environ.get('LOCALAPPDATA', '')) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft")
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("百应视频素材下载器 v1.0")
        self.setMinimumSize(1000, 700)

        self.products = {}  # name -> ProductData
        self.download_queue = queue.Queue()
        self.current_worker = None
        self.server_thread = None

        self._init_ui()
        self._load_settings()  # 加载保存的设置
        self._start_server()

    def _init_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 创建标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 产品列表标签页
        products_tab = self._create_products_tab()
        tabs.addTab(products_tab, "📦 产品列表")

        # 历史项目标签页
        history_tab = self._create_history_tab()
        tabs.addTab(history_tab, "📁 历史项目")

        # 设置标签页
        settings_tab = self._create_settings_tab()
        tabs.addTab(settings_tab, "⚙️ 下载设置")

        # 日志标签页
        log_tab = self._create_log_tab()
        tabs.addTab(log_tab, "📝 运行日志")

        # 底部状态栏
        self._create_status_bar()

    def _create_products_tab(self) -> QWidget:
        """创建产品列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.server_status = QLabel("🔴 服务器未启动")
        toolbar.addWidget(self.server_status)

        toolbar.addStretch()

        self.start_all_btn = QPushButton("▶️ 开始全部下载")
        self.start_all_btn.clicked.connect(self._start_all_downloads)
        toolbar.addWidget(self.start_all_btn)

        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self._stop_downloads)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)

        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.clicked.connect(self._clear_products)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # 产品表格
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(9)
        self.product_table.setHorizontalHeaderLabels([
            "产品名称", "佣金比例", "佣金赚", "价格", "月销", "评分", "综合得分", "状态", "操作"
        ])

        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 9):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.product_table)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return widget

    def _create_history_tab(self) -> QWidget:
        """创建历史项目标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self._refresh_history)
        toolbar.addWidget(refresh_btn)

        toolbar.addStretch()

        self.incomplete_only_check = QCheckBox("仅显示未完成项目")
        self.incomplete_only_check.stateChanged.connect(self._refresh_history)
        toolbar.addWidget(self.incomplete_only_check)

        layout.addLayout(toolbar)

        # 历史项目表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "产品名称", "状态", "搜索到", "已筛选", "已下载", "剪映", "创建时间", "操作"
        ])

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.history_table)

        # 项目详情区域
        details_group = QGroupBox("📋 项目详情")
        details_layout = QVBoxLayout(details_group)

        self.history_details_text = QTextEdit()
        self.history_details_text.setReadOnly(True)
        self.history_details_text.setMaximumHeight(150)
        self.history_details_text.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self.history_details_text)

        layout.addWidget(details_group)

        # 连接表格选择事件
        self.history_table.itemSelectionChanged.connect(self._on_history_selected)

        return widget

    def _refresh_history(self):
        """刷新历史项目列表"""
        if not ProjectManager:
            self._log("[历史] ProjectManager 模块未加载")
            return

        output_dir = self.output_dir_edit.text()
        manager = ProjectManager(output_dir)

        # 获取项目列表
        if self.incomplete_only_check.isChecked():
            projects = manager.get_incomplete_projects()
        else:
            projects = manager.list_projects()

        # 清空表格
        self.history_table.setRowCount(0)

        # 状态映射
        status_map = {
            'pending': '⏳ 等待中',
            'searching': '🔍 搜索中',
            'downloading': '⬇️ 下载中',
            'download_done': '✅ 下载完成',
            'editing': '✂️ 剪辑中',
            'edit_done': '🎬 剪辑完成',
            'uploading': '📤 上传中',
            'upload_done': '🎉 上传完成',
            'failed': '❌ 失败',
            'cancelled': '🚫 已取消'
        }

        for project in projects:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            # 产品名称
            self.history_table.setItem(row, 0, QTableWidgetItem(project.product_name))

            # 状态
            status_text = status_map.get(project.status, project.status)
            self.history_table.setItem(row, 1, QTableWidgetItem(status_text))

            # 搜索到的视频数
            self.history_table.setItem(row, 2, QTableWidgetItem(str(len(project.found_videos))))

            # 筛选后的视频数
            self.history_table.setItem(row, 3, QTableWidgetItem(str(len(project.filtered_videos))))

            # 已下载的视频数
            self.history_table.setItem(row, 4, QTableWidgetItem(str(len(project.downloaded_videos))))

            # 剪映项目
            jianying_status = "✅" if project.jianying_project_path else "—"
            self.history_table.setItem(row, 5, QTableWidgetItem(jianying_status))

            # 创建时间
            try:
                created = datetime.fromisoformat(project.created_at)
                created_str = created.strftime('%m-%d %H:%M')
            except:
                created_str = project.created_at[:16] if project.created_at else ''
            self.history_table.setItem(row, 6, QTableWidgetItem(created_str))

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(2)

            # 根据当前状态显示不同的操作按钮
            status = project.status

            # 🔍 搜索按钮 - 可以重新搜索
            search_btn = QPushButton("🔍")
            search_btn.setStyleSheet("padding: 2px 4px;")
            search_btn.setToolTip("重新搜索素材")
            search_btn.clicked.connect(lambda _, p=project: self._retry_step(p, 'search'))
            btn_layout.addWidget(search_btn)

            # ⬇️ 下载按钮 - 有筛选结果时可下载
            if len(project.filtered_videos) > 0 or status in ['downloading', 'download_done', 'editing', 'edit_done', 'uploading', 'upload_done']:
                download_btn = QPushButton("⬇️")
                download_btn.setStyleSheet("padding: 2px 4px;")
                download_btn.setToolTip("重新下载素材")
                download_btn.clicked.connect(lambda _, p=project: self._retry_step(p, 'download'))
                btn_layout.addWidget(download_btn)

            # ✂️ 剪辑按钮 - 有下载完成的视频时可剪辑
            if len(project.downloaded_videos) > 0 or status in ['editing', 'edit_done', 'uploading', 'upload_done']:
                edit_btn = QPushButton("✂️")
                edit_btn.setStyleSheet("padding: 2px 4px;")
                edit_btn.setToolTip("重新生成剪映项目")
                edit_btn.clicked.connect(lambda _, p=project: self._retry_step(p, 'edit'))
                btn_layout.addWidget(edit_btn)

            # 🎥 导出按钮 - 有剪映项目时可自动导出
            if project.jianying_project_path and HAS_JIANYING_CONTROLLER:
                export_btn = QPushButton("🎥")
                export_btn.setStyleSheet("padding: 2px 4px;")
                export_btn.setToolTip("自动导出视频（需打开剪映）")
                export_btn.clicked.connect(lambda _, p=project: self._retry_step(p, 'export'))
                btn_layout.addWidget(export_btn)

            # 📤 上传按钮 - 有剪映项目时可上传（预留）
            if project.jianying_project_path or status in ['uploading', 'upload_done']:
                upload_btn = QPushButton("📤")
                upload_btn.setStyleSheet("padding: 2px 4px;")
                upload_btn.setToolTip("上传到抖音（开发中）")
                upload_btn.clicked.connect(lambda _, p=project: self._retry_step(p, 'upload'))
                btn_layout.addWidget(upload_btn)

            # 分隔符
            btn_layout.addSpacing(4)

            # 📂 打开素材文件夹按钮
            open_btn = QPushButton("📂")
            open_btn.setStyleSheet("padding: 2px 4px;")
            open_btn.setToolTip("打开素材文件夹")
            open_btn.clicked.connect(lambda _, p=project: self._open_project_folder(p))
            btn_layout.addWidget(open_btn)

            # 🎬 打开剪映项目按钮（仅当剪映项目存在时显示）
            if project.jianying_project_path:
                open_jianying_btn = QPushButton("🎬")
                open_jianying_btn.setStyleSheet("padding: 2px 4px;")
                open_jianying_btn.setToolTip("打开剪映项目文件夹")
                open_jianying_btn.clicked.connect(lambda _, p=project: self._open_jianying_folder(p))
                btn_layout.addWidget(open_jianying_btn)

            self.history_table.setCellWidget(row, 7, btn_widget)

        self._log(f"[历史] 加载了 {len(projects)} 个项目")

    def _on_history_selected(self):
        """历史项目选中事件"""
        selected = self.history_table.selectedItems()
        if not selected:
            self.history_details_text.clear()
            return

        row = selected[0].row()
        product_name = self.history_table.item(row, 0).text()

        # 查找对应的项目
        if not ProjectManager:
            return

        output_dir = self.output_dir_edit.text()
        manager = ProjectManager(output_dir)
        projects = manager.list_projects()

        for project in projects:
            if project.product_name == product_name:
                # 显示项目详情
                details = []
                details.append(f"项目ID: {project.project_id}")
                details.append(f"产品名称: {project.product_name}")
                details.append(f"状态: {project.status}")
                details.append(f"项目目录: {project.project_dir}")
                details.append(f"创建时间: {project.created_at}")
                details.append(f"更新时间: {project.updated_at}")
                details.append(f"")
                details.append(f"搜索到视频: {len(project.found_videos)} 个")
                details.append(f"筛选后视频: {len(project.filtered_videos)} 个")
                details.append(f"已下载视频: {len(project.downloaded_videos)} 个")

                if project.jianying_project_path:
                    details.append(f"")
                    details.append(f"剪映项目: {project.jianying_project_path}")

                if project.error_message:
                    details.append(f"")
                    details.append(f"错误信息: {project.error_message}")

                self.history_details_text.setPlainText('\n'.join(details))
                break

    def _retry_step(self, project, step: str):
        """
        重试指定步骤

        Args:
            project: 项目配置
            step: 步骤名称 ('search', 'download', 'edit', 'upload')
        """
        self._log(f"[重试] 项目: {project.product_name}, 步骤: {step}")

        if step == 'search':
            # 重新搜索素材 - 从头开始整个流程
            product_data = ProductData({
                'name': project.product_name,
                'commission_rate': project.commission_rate,
                'commission_amount': project.commission_amount,
                'price': project.price,
                'monthly_sales': project.monthly_sales,
                'shop_score': project.shop_score,
                'totalScore': project.total_score,
                'project_dir': project.project_dir
            })

            # 清空之前的搜索结果
            project.found_videos = []
            project.filtered_videos = []
            project.status = ProjectStatus.PENDING
            project.save()

            # 添加到产品列表并开始下载
            if product_data.name not in self.products:
                self.products[product_data.name] = product_data
                self._add_product_to_table(product_data)

            self.download_queue.put(product_data)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(1)
            self.progress_bar.setValue(0)
            self.start_all_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self._process_next_download()

        elif step == 'download':
            # 重新下载素材 - 使用已筛选的视频列表
            if not project.filtered_videos:
                self._log(f"[重试] 没有筛选的视频可供下载，请先搜索")
                QMessageBox.warning(self, "提示", "没有筛选的视频可供下载，请先点击🔍搜索素材")
                return

            # 清空已下载列表，准备重新下载
            project.downloaded_videos = []
            project.status = ProjectStatus.DOWNLOADING
            project.save()

            self._log(f"[重试] 开始重新下载 {len(project.filtered_videos)} 个视频...")
            self._download_filtered_videos(project)

        elif step == 'edit':
            # 重新生成剪映项目
            if not project.downloaded_videos and not list(Path(project.project_dir).glob("*.mp4")):
                self._log(f"[重试] 没有下载的视频，无法生成剪映项目")
                QMessageBox.warning(self, "提示", "没有下载的视频，请先点击⬇️下载素材")
                return

            if not JianyingGenerator:
                self._log(f"[重试] JianyingGenerator 模块未加载")
                QMessageBox.warning(self, "错误", "剪映生成器模块未加载")
                return

            project.status = ProjectStatus.EDITING
            project.save()

            video_dir = Path(project.project_dir)
            jianying_path = self._generate_jianying_for_project(video_dir, project.product_name)
            if jianying_path:
                project.jianying_project_path = jianying_path
                project.jianying_created_at = datetime.now().isoformat()
                project.status = ProjectStatus.EDIT_DONE
                project.save()
                self._log(f"[重试] 剪映项目生成成功: {jianying_path}")
            else:
                project.status = ProjectStatus.FAILED
                project.error_message = "剪映项目生成失败"
                project.save()
                self._log(f"[重试] 剪映项目生成失败")

            self._refresh_history()

        elif step == 'export':
            # 自动导出剪映项目
            if not project.jianying_project_path:
                self._log(f"[导出] 没有剪映项目，无法导出")
                QMessageBox.warning(self, "提示", "没有剪映项目，请先点击✂️生成剪映项目")
                return

            if not HAS_JIANYING_CONTROLLER:
                self._log(f"[导出] pyJianYingDraft 模块未加载，无法自动导出")
                QMessageBox.warning(self, "错误", "自动导出功能不可用，请安装 pyJianYingDraft: pip install pyJianYingDraft")
                return

            # 在后台线程执行导出
            self._export_jianying_project(project)

        elif step == 'upload':
            # 上传到抖音（预留功能）
            if not project.jianying_project_path:
                self._log(f"[重试] 没有剪映项目，无法上传")
                QMessageBox.warning(self, "提示", "没有剪映项目，请先点击✂️生成剪映项目")
                return

            self._log(f"[上传] 上传到抖音功能开发中...")
            QMessageBox.information(self, "提示", "上传到抖音功能正在开发中，敬请期待！")
            # TODO: 实现抖音上传功能
            # project.status = ProjectStatus.UPLOADING
            # project.save()
            # self._upload_to_douyin(project)

    def _is_jianying_running(self) -> bool:
        """检查剪映是否正在运行"""
        import subprocess
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq JianyingPro.exe'],
                capture_output=True, text=True, timeout=5
            )
            return 'JianyingPro.exe' in result.stdout
        except Exception:
            return False

    def _kill_jianying(self) -> bool:
        """关闭剪映进程"""
        import subprocess
        import time as time_module
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'JianyingPro.exe'],
                          capture_output=True, timeout=10)
            time_module.sleep(2)  # 等待进程完全关闭
            return True
        except Exception as e:
            self._log(f"[导出] 关闭剪映失败: {e}")
            return False

    def _find_jianying_path(self) -> str:
        """查找剪映安装路径"""
        import os
        possible_paths = [
            os.path.expandvars(r'%LocalAppData%\JianyingPro\Apps\JianyingPro.exe'),
            os.path.expandvars(r'%ProgramFiles%\JianyingPro\JianyingPro.exe'),
            r'C:\Program Files\JianyingPro\JianyingPro.exe',
            os.path.expandvars(r'%USERPROFILE%\AppData\Local\JianyingPro\Apps\JianyingPro.exe'),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 尝试从注册表查找
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\JianyingPro')
            install_path, _ = winreg.QueryValueEx(key, 'InstallLocation')
            winreg.CloseKey(key)
            exe_path = os.path.join(install_path, 'JianyingPro.exe')
            if os.path.exists(exe_path):
                return exe_path
        except Exception:
            pass

        return None

    def _start_jianying(self) -> bool:
        """启动剪映"""
        import subprocess

        # 优先使用设置中的路径
        settings = self._get_settings()
        jianying_path = settings.get('jianying_app_path', '')

        # 如果设置中没有，尝试自动检测
        if not jianying_path or not os.path.exists(jianying_path):
            jianying_path = self._find_jianying_path()

        if not jianying_path:
            self._log("[导出] 未找到剪映安装路径，请在设置中指定剪映程序路径")
            return False

        try:
            self._log(f"[导出] 启动剪映: {jianying_path}")
            subprocess.Popen([jianying_path], shell=True)
            return True
        except Exception as e:
            self._log(f"[导出] 启动剪映失败: {e}")
            return False

    def _wait_for_jianying_window(self, timeout: int = 60) -> bool:
        """
        等待剪映窗口出现（自动检测）

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否成功检测到剪映窗口
        """
        import time as time_module
        try:
            import uiautomation as uia
        except ImportError:
            self._log("[导出] uiautomation 未安装，无法自动检测剪映窗口")
            return False

        start_time = time_module.time()
        self._log(f"[导出] 等待剪映窗口出现（最长 {timeout} 秒）...")

        while time_module.time() - start_time < timeout:
            try:
                # 查找剪映主页窗口
                window = uia.WindowControl(searchDepth=1, Name="剪映专业版")
                if window.Exists(0.5):
                    # 检查是否是首页（HomePage）
                    if "HomePage".lower() in window.ClassName.lower():
                        self._log("[导出] 检测到剪映首页窗口")
                        return True
                    # 或者主窗口
                    if "MainWindow".lower() in window.ClassName.lower():
                        self._log("[导出] 检测到剪映编辑窗口")
                        return True
            except Exception as e:
                if self._get_settings().get('debug'):
                    print(f"[DEBUG] 检测剪映窗口异常: {e}")

            time_module.sleep(1)
            elapsed = int(time_module.time() - start_time)
            if elapsed % 5 == 0:
                self._log(f"[导出] 等待剪映启动... ({elapsed}/{timeout}秒)")

        self._log("[导出] 等待剪映窗口超时")
        return False

    def _export_jianying_project(self, project, auto_start=True):
        """
        自动导出剪映项目（在后台线程中执行，不阻塞UI）

        Args:
            project: 项目配置
            auto_start: 是否自动启动剪映（默认True）
        """
        # 检查是否已有导出任务在运行
        if hasattr(self, 'export_worker') and self.export_worker is not None and self.export_worker.isRunning():
            QMessageBox.warning(self, "提示", "已有导出任务正在运行，请等待完成后再试")
            return

        self._log(f"[导出] 启动后台导出任务: {project.product_name}")

        # 创建导出工作线程
        settings = self._get_settings()
        self.export_worker = ExportWorker(project, settings)
        self.export_worker.log.connect(self._log)
        self.export_worker.progress.connect(self._on_export_progress)
        self.export_worker.finished.connect(lambda success, msg: self._on_export_finished(success, msg, project))
        self.export_worker.start()

    def _on_export_progress(self, status: str):
        """导出进度回调"""
        self.statusBar().showMessage(f"导出中: {status}")

    def _on_export_finished(self, success: bool, message: str, project):
        """导出完成回调"""
        self.statusBar().clearMessage()

        if success:
            self._log(f"[导出] 成功: {message}")
            QMessageBox.information(self, "导出成功", f"视频已导出到：\n{message}")

            # 更新项目状态
            project.status = ProjectStatus.UPLOAD_DONE
            project.save()
            self._refresh_history()
        else:
            self._log(f"[导出] 失败: {message}")
            QMessageBox.critical(
                self,
                "导出失败",
                f"自动导出失败：\n{message}\n\n"
                f"可能的原因：\n"
                f"1. 剪映未正确打开或不在草稿列表页\n"
                f"2. 找不到指定的草稿项目\n"
                f"3. 剪映版本不兼容（需要v6及以下）\n\n"
                f"请检查后重试。"
            )

    def _download_filtered_videos(self, project):
        """下载已筛选的视频列表"""
        # 创建下载任务
        product_data = ProductData({
            'name': project.product_name,
            'commission_rate': project.commission_rate,
            'commission_amount': project.commission_amount,
            'price': project.price,
            'monthly_sales': project.monthly_sales,
            'shop_score': project.shop_score,
            'totalScore': project.total_score,
            'project_dir': project.project_dir
        })
        product_data.project_config = project

        # 添加到产品列表
        if product_data.name not in self.products:
            self.products[product_data.name] = product_data
            self._add_product_to_table(product_data)

        self.download_queue.put(product_data)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        self.start_all_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._process_next_download()

    def _continue_project(self, project):
        """继续未完成的项目（根据当前状态自动选择步骤）"""
        self._log(f"[继续] 项目: {project.product_name}")

        # 根据项目状态决定继续的步骤
        if project.status in ['pending', 'searching', 'downloading']:
            self._retry_step(project, 'search')

        elif project.status == 'download_done':
            self._retry_step(project, 'edit')

        elif project.status == 'editing':
            self._retry_step(project, 'edit')

        elif project.status == 'edit_done':
            self._retry_step(project, 'upload')

    def _generate_jianying_for_project(self, video_dir: Path, product_name: str) -> str:
        """为项目生成剪映项目（从历史项目继续时使用）"""
        settings = self._get_settings()

        try:
            template_path = settings.get('jianying_template', '')
            if not template_path or not Path(template_path).exists():
                self._log(f"[剪映] 模板路径无效")
                return None

            video_files = sorted(video_dir.glob("*.mp4"))
            if not video_files:
                self._log(f"[剪映] 未找到视频文件")
                return None

            self._log(f"[剪映] 正在生成项目，使用 {len(video_files)} 个视频...")

            draft_output_dir = settings.get('jianying_draft_dir', '')
            generator = JianyingGenerator(template_path, output_base_dir=draft_output_dir if draft_output_dir else None)

            safe_name = self._safe_filename(product_name[:20])
            timestamp = datetime.now().strftime('%m%d_%H%M%S')
            project_name = f"{safe_name}_{timestamp}"

            project_path = generator.generate_project(
                video_files=[str(f) for f in video_files],
                project_name=project_name,
                auto_open=False
            )

            self._log(f"[剪映] 项目已生成: {project_path}")
            return project_path

        except Exception as e:
            self._log(f"[剪映] 生成失败: {e}")
            return None

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def _open_project_folder(self, project):
        """打开素材文件夹（项目文件夹）"""
        import subprocess
        project_dir = Path(project.project_dir)
        if project_dir.exists():
            subprocess.Popen(f'explorer "{project_dir}"', shell=True)
        else:
            QMessageBox.warning(self, "错误", f"素材文件夹不存在: {project_dir}")

    def _open_jianying_folder(self, project):
        """打开剪映项目文件夹"""
        import subprocess
        jianying_path = Path(project.jianying_project_path)
        if jianying_path.exists():
            subprocess.Popen(f'explorer "{jianying_path}"', shell=True)
        else:
            QMessageBox.warning(self, "错误", f"剪映项目文件夹不存在: {jianying_path}")

    def _create_settings_tab(self) -> QWidget:
        """创建设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 服务器设置
        server_group = QGroupBox("🌐 服务器设置")
        server_layout = QFormLayout(server_group)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(5000)
        server_layout.addRow("监听端口:", self.port_spin)

        self.auto_download_check = QCheckBox("收到产品后自动开始下载")
        self.auto_download_check.setChecked(True)
        server_layout.addRow(self.auto_download_check)

        layout.addWidget(server_group)

        # 视频筛选设置
        filter_group = QGroupBox("🎬 视频筛选条件")
        filter_layout = QFormLayout(filter_group)

        self.min_duration_spin = QDoubleSpinBox()
        self.min_duration_spin.setRange(0, 600)
        self.min_duration_spin.setValue(15)
        self.min_duration_spin.setSuffix(" 秒")
        filter_layout.addRow("最小视频时长:", self.min_duration_spin)

        self.max_duration_spin = QDoubleSpinBox()
        self.max_duration_spin.setRange(0, 600)
        self.max_duration_spin.setValue(60)
        self.max_duration_spin.setSuffix(" 秒")
        filter_layout.addRow("最大视频时长:", self.max_duration_spin)

        self.min_likes_spin = QSpinBox()
        self.min_likes_spin.setRange(0, 10000000)
        self.min_likes_spin.setValue(1000)
        self.min_likes_spin.setSingleStep(100)
        filter_layout.addRow("最小点赞数:", self.min_likes_spin)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["点赞+最新 (digg_time)", "点赞最高 (digg)", "最新发布 (time)"])
        filter_layout.addRow("排序方式:", self.sort_combo)

        layout.addWidget(filter_group)

        # 下载设置
        download_group = QGroupBox("📥 下载设置")
        download_layout = QFormLayout(download_group)

        self.download_count_spin = QSpinBox()
        self.download_count_spin.setRange(1, 20)
        self.download_count_spin.setValue(3)
        download_layout.addRow("每产品下载视频数:", self.download_count_spin)

        self.scroll_times_spin = QSpinBox()
        self.scroll_times_spin.setRange(0, 10)
        self.scroll_times_spin.setValue(5)
        download_layout.addRow("页面滚动次数:", self.scroll_times_spin)

        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(str(Path.home() / "Downloads" / "baiying_videos"))
        output_layout.addWidget(self.output_dir_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(browse_btn)

        download_layout.addRow("保存目录:", output_layout)

        self.headless_check = QCheckBox("无头模式（不显示浏览器窗口）")
        self.headless_check.setChecked(True)
        download_layout.addRow(self.headless_check)

        self.debug_check = QCheckBox("调试模式")
        download_layout.addRow(self.debug_check)

        layout.addWidget(download_group)

        # 剪映设置
        jianying_group = QGroupBox("🎬 剪映自动剪辑")
        jianying_layout = QFormLayout(jianying_group)

        self.auto_jianying_check = QCheckBox("下载完成后自动生成剪映项目")
        self.auto_jianying_check.setChecked(False)
        jianying_layout.addRow(self.auto_jianying_check)

        template_layout = QHBoxLayout()
        self.jianying_template_edit = QLineEdit()
        self.jianying_template_edit.setPlaceholderText("选择剪映模板文件夹...")
        # 默认使用 MB12.15 模板
        default_template = Path(__file__).parent / "MB12.15"
        if default_template.exists():
            self.jianying_template_edit.setText(str(default_template))
        template_layout.addWidget(self.jianying_template_edit)

        template_browse_btn = QPushButton("浏览...")
        template_browse_btn.clicked.connect(self._browse_jianying_template)
        template_layout.addWidget(template_browse_btn)

        jianying_layout.addRow("剪映模板:", template_layout)

        # 剪映草稿输出目录
        draft_layout = QHBoxLayout()
        self.jianying_draft_dir_edit = QLineEdit()
        # 默认剪映草稿目录
        default_draft_dir = Path(os.environ.get('LOCALAPPDATA', '')) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft"
        if default_draft_dir.exists():
            self.jianying_draft_dir_edit.setText(str(default_draft_dir))
        else:
            self.jianying_draft_dir_edit.setPlaceholderText("选择剪映草稿输出目录...")
        draft_layout.addWidget(self.jianying_draft_dir_edit)

        draft_browse_btn = QPushButton("浏览...")
        draft_browse_btn.clicked.connect(self._browse_jianying_draft_dir)
        draft_layout.addWidget(draft_browse_btn)

        jianying_layout.addRow("草稿输出目录:", draft_layout)

        # 剪映应用程序路径
        app_layout = QHBoxLayout()
        self.jianying_app_path_edit = QLineEdit()
        self.jianying_app_path_edit.setPlaceholderText("选择剪映应用程序路径 (JianyingPro.exe)...")
        # 尝试自动检测剪映路径
        default_app_path = self._find_jianying_path()
        if default_app_path:
            self.jianying_app_path_edit.setText(default_app_path)
        app_layout.addWidget(self.jianying_app_path_edit)

        app_browse_btn = QPushButton("浏览...")
        app_browse_btn.clicked.connect(self._browse_jianying_app)
        app_layout.addWidget(app_browse_btn)

        jianying_layout.addRow("剪映程序路径:", app_layout)

        layout.addWidget(jianying_group)

        # 保存按钮
        save_btn = QPushButton("💾 保存设置")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        return widget

    def _create_log_tab(self) -> QWidget:
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(clear_log_btn)

        return widget

    def _create_status_bar(self):
        """创建状态栏"""
        self.statusBar().showMessage("就绪")

    def _start_server(self):
        """启动HTTP服务器"""
        port = self.port_spin.value()
        self.server_thread = ServerThread(port)
        self.server_thread.product_received.connect(self._on_products_received)
        self.server_thread.log.connect(self._log)
        self.server_thread.start()

        self.server_status.setText(f"🟢 服务器运行中 (端口: {port})")
        self._log(f"服务器已启动，监听端口: {port}")

    def _on_products_received(self, data: dict):
        """收到产品数据"""
        products = data.get('products', [])
        source = data.get('source', 'unknown')
        timestamp = data.get('timestamp', '')

        self._log(f"收到 {len(products)} 个产品 (来源: {source})")

        # 添加到表格
        for p_data in products:
            product = ProductData(p_data)
            if product.name not in self.products:
                self.products[product.name] = product
                self._add_product_to_table(product)

        # 自动开始下载
        if self.auto_download_check.isChecked() and products:
            self._start_all_downloads()

    def _add_product_to_table(self, product: ProductData):
        """添加产品到表格"""
        row = self.product_table.rowCount()
        self.product_table.insertRow(row)

        self.product_table.setItem(row, 0, QTableWidgetItem(product.name))
        self.product_table.setItem(row, 1, QTableWidgetItem(product.commission_rate))
        self.product_table.setItem(row, 2, QTableWidgetItem(product.commission_amount))
        self.product_table.setItem(row, 3, QTableWidgetItem(product.price))
        self.product_table.setItem(row, 4, QTableWidgetItem(product.monthly_sales))
        self.product_table.setItem(row, 5, QTableWidgetItem(product.shop_score))
        self.product_table.setItem(row, 6, QTableWidgetItem(f"{product.total_score:.1f}"))
        self.product_table.setItem(row, 7, QTableWidgetItem("⏳ 等待中"))
        self.product_table.setItem(row, 8, QTableWidgetItem(""))  # 操作列占位

    def _add_retry_button(self, row: int, product_name: str):
        """为指定行添加重试按钮"""
        retry_btn = QPushButton("🔄 重试")
        retry_btn.setStyleSheet("padding: 2px 8px;")
        retry_btn.clicked.connect(lambda _, name=product_name: self._retry_product(name))
        self.product_table.setCellWidget(row, 8, retry_btn)

    def _remove_retry_button(self, row: int):
        """移除指定行的重试按钮"""
        self.product_table.removeCellWidget(row, 8)
        self.product_table.setItem(row, 8, QTableWidgetItem(""))

    def _retry_product(self, product_name: str):
        """重试下载指定产品"""
        if product_name not in self.products:
            self._log(f"[错误] 找不到产品: {product_name}")
            return

        product = self.products[product_name]

        # 增加重试计数
        product.retry_count += 1

        # 重置状态
        product.status = 'pending'
        product.videos_downloaded = 0

        # 更新表格状态
        for row in range(self.product_table.rowCount()):
            if self.product_table.item(row, 0).text() == product_name:
                self.product_table.setItem(row, 7, QTableWidgetItem(f"⏳ 等待重试 #{product.retry_count}"))
                self._remove_retry_button(row)
                break

        self._log(f"[重试] 产品 '{product_name}' 已加入重试队列 (第 {product.retry_count} 次)")

        # 如果当前没有下载任务在运行，立即开始
        if self.download_queue.empty() and (self.current_worker is None or not self.current_worker.isRunning()):
            self.download_queue.put(product)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(1)
            self.progress_bar.setValue(0)
            self.start_all_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self._process_next_download()
        else:
            # 加入队列等待
            self.download_queue.put(product)

    def _get_settings(self) -> dict:
        """获取当前设置"""
        sort_map = {
            0: 'digg_time',
            1: 'digg',
            2: 'time'
        }
        return {
            'min_duration': self.min_duration_spin.value(),
            'max_duration': self.max_duration_spin.value(),
            'min_likes': self.min_likes_spin.value(),
            'sort_by': sort_map.get(self.sort_combo.currentIndex(), 'digg_time'),
            'download_count': self.download_count_spin.value(),
            'scroll_times': self.scroll_times_spin.value(),
            'output_dir': self.output_dir_edit.text(),
            'headless': self.headless_check.isChecked(),
            'debug': self.debug_check.isChecked(),
            'auto_jianying': self.auto_jianying_check.isChecked(),
            'jianying_template': self.jianying_template_edit.text(),
            'jianying_draft_dir': self.jianying_draft_dir_edit.text(),
            'jianying_app_path': self.jianying_app_path_edit.text()
        }

    def _start_all_downloads(self):
        """开始下载所有产品"""
        pending_products = [p for p in self.products.values() if p.status == 'pending']

        if not pending_products:
            self._log("没有待下载的产品")
            return

        self._log(f"开始下载 {len(pending_products)} 个产品的视频...")

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(pending_products))
        self.progress_bar.setValue(0)

        self.start_all_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 将产品加入队列
        for product in pending_products:
            self.download_queue.put(product)

        # 开始处理队列
        self._process_next_download()

    def _process_next_download(self):
        """处理下一个下载任务"""
        if self.download_queue.empty():
            self._log("所有下载任务完成")
            self.start_all_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            return

        product = self.download_queue.get()
        settings = self._get_settings()

        self.current_worker = DownloadWorker(product, settings)
        self.current_worker.progress.connect(self._on_download_progress)
        self.current_worker.log.connect(self._log)
        self.current_worker.finished_product.connect(self._on_product_finished)
        self.current_worker.start()

    def _on_download_progress(self, product_name: str, status: str, video_count: int):
        """下载进度更新"""
        # 更新表格状态
        for row in range(self.product_table.rowCount()):
            if self.product_table.item(row, 0).text() == product_name:
                status_map = {
                    'downloading': f"⬇️ 下载中 ({video_count})",
                    'completed': f"✅ 完成 ({video_count})",
                    'failed': "❌ 失败"
                }
                self.product_table.setItem(row, 7, QTableWidgetItem(status_map.get(status, status)))

                # 任务结束时（完成或失败）添加重试按钮
                if status in ['completed', 'failed']:
                    self._add_retry_button(row, product_name)
                break

        # 更新产品状态
        if product_name in self.products:
            self.products[product_name].status = status
            self.products[product_name].videos_downloaded = video_count

    def _on_product_finished(self, product_name: str):
        """产品下载完成"""
        completed = sum(1 for p in self.products.values() if p.status in ['completed', 'failed'])
        self.progress_bar.setValue(completed)

        # 处理下一个
        self._process_next_download()

    def _stop_downloads(self):
        """停止下载"""
        self._log("正在停止下载...")

        # 清空队列
        while not self.download_queue.empty():
            try:
                self.download_queue.get_nowait()
            except:
                break

        # 停止当前工作线程
        if self.current_worker:
            self.current_worker.stop()

        self.start_all_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

    def _clear_products(self):
        """清空产品列表"""
        self.products.clear()
        self.product_table.setRowCount(0)
        self._log("已清空产品列表")

    def _browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def _browse_jianying_template(self):
        """浏览剪映模板目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择剪映模板文件夹")
        if dir_path:
            # 验证是否是有效的剪映模板
            if Path(dir_path, "draft_content.json").exists():
                self.jianying_template_edit.setText(dir_path)
            else:
                QMessageBox.warning(self, "无效模板", "所选文件夹不是有效的剪映模板（未找到 draft_content.json）")

    def _browse_jianying_draft_dir(self):
        """浏览剪映草稿输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择剪映草稿输出目录")
        if dir_path:
            self.jianying_draft_dir_edit.setText(dir_path)

    def _browse_jianying_app(self):
        """浏览剪映应用程序路径"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择剪映应用程序",
            os.environ.get('LOCALAPPDATA', ''),
            "可执行文件 (*.exe)"
        )
        if file_path:
            self.jianying_app_path_edit.setText(file_path)

    def _load_settings(self):
        """从文件加载设置"""
        settings = self.DEFAULT_SETTINGS.copy()

        try:
            if self.SETTINGS_FILE.exists():
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    settings.update(saved)
                self._log(f"已加载设置文件: {self.SETTINGS_FILE}")
        except Exception as e:
            self._log(f"加载设置文件失败: {e}，使用默认设置")

        # 应用设置到UI控件
        self._apply_settings_to_ui(settings)

    def _apply_settings_to_ui(self, settings: dict):
        """将设置应用到UI控件"""
        # 服务器设置
        self.port_spin.setValue(settings.get('port', 5000))
        self.auto_download_check.setChecked(settings.get('auto_download', True))

        # 视频筛选设置
        self.min_duration_spin.setValue(settings.get('min_duration', 15))
        self.max_duration_spin.setValue(settings.get('max_duration', 60))
        self.min_likes_spin.setValue(settings.get('min_likes', 1000))

        # 排序方式
        sort_map = {'digg_time': 0, 'digg': 1, 'time': 2}
        sort_index = sort_map.get(settings.get('sort_by', 'digg_time'), 0)
        self.sort_combo.setCurrentIndex(sort_index)

        # 下载设置
        self.download_count_spin.setValue(settings.get('download_count', 3))
        self.scroll_times_spin.setValue(settings.get('scroll_times', 5))
        self.output_dir_edit.setText(settings.get('output_dir', str(Path.home() / "Downloads" / "baiying_videos")))
        self.headless_check.setChecked(settings.get('headless', True))
        self.debug_check.setChecked(settings.get('debug', False))

        # 剪映设置
        self.auto_jianying_check.setChecked(settings.get('auto_jianying', False))
        jianying_template = settings.get('jianying_template', '')
        if jianying_template:
            self.jianying_template_edit.setText(jianying_template)
        jianying_draft_dir = settings.get('jianying_draft_dir', '')
        if jianying_draft_dir:
            self.jianying_draft_dir_edit.setText(jianying_draft_dir)
        jianying_app_path = settings.get('jianying_app_path', '')
        if jianying_app_path:
            self.jianying_app_path_edit.setText(jianying_app_path)

    def _save_settings(self):
        """保存设置到文件"""
        settings = self._get_settings()

        # 添加服务器相关设置
        settings['port'] = self.port_spin.value()
        settings['auto_download'] = self.auto_download_check.isChecked()

        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self._log(f"设置已保存到: {self.SETTINGS_FILE}")
            QMessageBox.information(self, "提示", "设置已保存")
        except Exception as e:
            self._log(f"保存设置失败: {e}")
            QMessageBox.warning(self, "错误", f"保存设置失败: {e}")

    def _log(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.statusBar().showMessage(message)

    def closeEvent(self, event):
        """关闭事件"""
        # 自动保存设置
        self._save_settings_silent()

        if self.current_worker:
            self.current_worker.stop()
            self.current_worker.wait()
        event.accept()

    def _save_settings_silent(self):
        """静默保存设置（不弹窗）"""
        settings = self._get_settings()
        settings['port'] = self.port_spin.value()
        settings['auto_download'] = self.auto_download_check.isChecked()

        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 静默失败


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
