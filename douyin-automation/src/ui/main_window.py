"""主窗口"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QPushButton, QLabel, QLineEdit,
    QComboBox, QTextEdit, QProgressBar, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QStatusBar, QToolBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont

from core.config import Config
from core.account_manager import AccountManager
from core.browser_manager import BrowserManager
from workflow.pipeline import Pipeline
from models.project import ProjectStatus
from models.video import ExportedVideo
from platforms.douyin import DouyinUploader

TEST_ASSET_DIR = r"C:\Users\21346\OneDrive\桌面\jianying_test"


class WorkerThread(QThread):
    """工作线程 - 执行 Pipeline 任务"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int, int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, pipeline: Pipeline, account_id: str, product_url: str, project_name: str = None):
        super().__init__()
        self.pipeline = pipeline
        self.account_id = account_id
        self.product_url = product_url
        self.project_name = project_name

    def run(self):
        try:
            # 设置回调
            self.pipeline.on_log = lambda msg: self.log_signal.emit(msg)
            self.pipeline.on_progress = lambda step, cur, total: self.progress_signal.emit(step, cur, total)
            self.pipeline.on_status_change = lambda p: self.status_signal.emit(p.status)

            project = self.pipeline.run(
                account_id=self.account_id,
                product_url=self.product_url,
                project_name=self.project_name
            )

            if project and project.status == ProjectStatus.COMPLETED.value:
                self.finished_signal.emit(True, "项目完成!")
            else:
                error = project.error_message if project else "未知错误"
                self.finished_signal.emit(False, f"项目失败: {error}")

        except Exception as e:
            self.finished_signal.emit(False, f"错误: {str(e)}")


class JianyingUploadThread(QThread):
    """测试线程 - 从剪映剪辑到上传抖音"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int, int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, pipeline: Pipeline, account_id: str, video_paths: list, image_paths: list, project_name: str = None):
        super().__init__()
        self.pipeline = pipeline
        self.account_id = account_id
        self.video_paths = video_paths
        self.image_paths = image_paths
        self.project_name = project_name

    def run(self):
        try:
            self.pipeline.on_log = lambda msg: self.log_signal.emit(msg)
            self.pipeline.on_progress = lambda step, cur, total: self.progress_signal.emit(step, cur, total)
            self.pipeline.on_status_change = lambda p: self.status_signal.emit(p.status)

            project = self.pipeline.run_from_videos(
                account_id=self.account_id,
                video_paths=self.video_paths,
                image_paths=self.image_paths,
                project_name=self.project_name
            )

            if project and project.status == ProjectStatus.COMPLETED.value:
                self.finished_signal.emit(True, "测试流程完成!")
            else:
                error = project.error_message if project else "未知错误"
                self.finished_signal.emit(False, f"测试失败: {error}")

        except Exception as e:
            self.finished_signal.emit(False, f"错误: {str(e)}")


class UploadOnlyThread(QThread):
    """测试线程 - 仅上传视频到抖音"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, account_manager, config: Config, account_id: str, video_path: str, cover_paths: list):
        super().__init__()
        self.account_manager = account_manager
        self.config = config
        self.account_id = account_id
        self.video_path = video_path
        self.cover_paths = cover_paths

    def run(self):
        try:
            browser_manager = BrowserManager(self.account_manager)
            uploader = DouyinUploader(browser_manager, self.account_id, self.config)

            uploader.start()

            if not uploader.is_logged_in():
                self.log_signal.emit("请在浏览器中登录抖音创作者中心...")
                if not uploader.wait_for_login():
                    self.finished_signal.emit(False, "登录超时")
                    return

            video = ExportedVideo(video_id="upload_test", local_path=self.video_path)
            success = uploader.upload_video(video, cover_paths=self.cover_paths, on_log=self.log_signal.emit)
            if success:
                self.finished_signal.emit(True, "上传测试完成!")
            else:
                self.finished_signal.emit(False, "上传测试失败")
        except Exception as e:
            self.finished_signal.emit(False, f"错误: {str(e)}")
        finally:
            try:
                uploader.close()
            except Exception:
                pass


class BrowserThread(QThread):
    """浏览器操作线程 - 避免阻塞 UI"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, account_manager, account_id: str, platform: str):
        super().__init__()
        self.account_manager = account_manager
        self.account_id = account_id
        self.platform = platform

    def run(self):
        try:
            from core.browser_manager import BrowserManager
            browser_manager = BrowserManager(self.account_manager)

            platform_names = {
                'baiying': '百应',
                'douyin': '抖音',
                'douyin_creator': '抖音创作者中心'
            }

            self.log_signal.emit(f"正在启动浏览器并打开 {platform_names[self.platform]}...")
            browser_manager.navigate_to_platform(self.account_id, self.platform)
            self.finished_signal.emit(True, f"{platform_names[self.platform]} 登录页面已打开")

        except Exception as e:
            self.finished_signal.emit(False, f"打开浏览器失败: {str(e)}")


class ProfileExportThread(QThread):
    """Profile 导出线程"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, account_manager, account_id: str, platform: str, output_path: str):
        super().__init__()
        self.account_manager = account_manager
        self.account_id = account_id
        self.platform = platform
        self.output_path = output_path

    def run(self):
        try:
            from core.browser_manager import BrowserManager
            from pathlib import Path

            browser_manager = BrowserManager(self.account_manager)
            self.log_signal.emit(f"正在导出 {self.platform} profile...")

            zip_path = browser_manager.export_profile(
                self.account_id,
                self.platform,
                Path(self.output_path)
            )

            self.finished_signal.emit(True, str(zip_path))

        except Exception as e:
            self.finished_signal.emit(False, f"导出失败: {str(e)}")


class ProfileImportThread(QThread):
    """Profile 导入线程"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, account_manager, account_id: str, platform: str, zip_path: str):
        super().__init__()
        self.account_manager = account_manager
        self.account_id = account_id
        self.platform = platform
        self.zip_path = zip_path

    def run(self):
        try:
            from core.browser_manager import BrowserManager
            from pathlib import Path

            browser_manager = BrowserManager(self.account_manager)
            self.log_signal.emit(f"正在导入 {self.platform} profile...")

            browser_manager.import_profile(
                self.account_id,
                self.platform,
                Path(self.zip_path)
            )

            self.finished_signal.emit(True, f"Profile 已成功导入到 {self.platform}")

        except Exception as e:
            self.finished_signal.emit(False, f"导入失败: {str(e)}")


class PickingThread(QThread):
    """百应选品线程 - 打开百应进行智能选品，登录后自动导航、筛选、选品并下载素材，然后搜索抖音视频"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int, int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, account_manager, account_id: str, config=None):
        super().__init__()
        self.account_manager = account_manager
        self.account_id = account_id
        self.config = config

    def run(self):
        try:
            from core.browser_manager import BrowserManager
            from platforms.baiying.picker import BaiyingPicker

            browser_manager = BrowserManager(self.account_manager)
            self.log_signal.emit("正在打开百应登录页面...")

            # 创建 picker 实例
            picker = BaiyingPicker(browser_manager, self.account_id, self.config)
            picker.start()

            self.log_signal.emit("请在浏览器中完成登录...")
            self.log_signal.emit("登录成功后将自动进入选品页面并应用筛选条件")

            # 等待登录并自动导航到选品页面
            if not picker.wait_for_login_and_navigate(
                timeout=300,
                on_log=lambda msg: self.log_signal.emit(msg)
            ):
                self.finished_signal.emit(False, "登录超时或进入选品页面失败")
                return

            # 获取配置
            n = self.config.get('picking.product_count', 3) if self.config else 3
            output_base = self.config.get('output.base_dir', '') if self.config else ''
            if not output_base:
                output_base = str(Path.home() / "Downloads" / "douyin-automation")
            output_dir = Path(output_base) / "materials"
            output_dir.mkdir(parents=True, exist_ok=True)

            self.log_signal.emit(f"\n开始自动选品，目标数量: {n}")
            self.log_signal.emit(f"素材输出目录: {output_dir}")

            # 自动选品并下载素材
            products = picker.auto_pick_products(
                n=n,
                output_dir=output_dir,
                on_log=lambda msg: self.log_signal.emit(msg),
                on_progress=lambda step, cur, total: self.progress_signal.emit(step, cur, total)
            )

            if not products:
                self.finished_signal.emit(False, "未能成功处理任何产品")
                return

            self.log_signal.emit(f"\n百应选品完成！成功处理 {len(products)} 个产品")

            # ========== 阶段2: 关闭百应，打开抖音搜索视频 ==========
            self.log_signal.emit("\n" + "=" * 60)
            self.log_signal.emit("阶段2: 抖音视频搜索")
            self.log_signal.emit("=" * 60)

            # 关闭百应浏览器
            self.log_signal.emit("关闭百应浏览器...")
            picker.close()

            # 为每个产品搜索并下载抖音视频
            self._search_and_download_douyin_videos(
                browser_manager, products, output_dir
            )

            self.finished_signal.emit(
                True,
                f"全流程完成！\n成功处理 {len(products)} 个产品\n素材已保存到: {output_dir}"
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished_signal.emit(False, f"选品流程失败: {str(e)}")

    def _search_and_download_douyin_videos(
        self,
        browser_manager,
        products,
        output_dir: Path
    ):
        """搜索并下载抖音视频

        Args:
            browser_manager: 浏览器管理器
            products: 产品列表
            output_dir: 输出目录
        """
        import re
        import urllib.parse
        from platforms.douyin.searcher import DouyinSearcher
        from platforms.douyin.downloader import VideoDownloader

        # 获取抖音视频筛选配置 (使用点号路径)
        min_duration = self.config.get('douyin_video.min_duration', 45) if self.config else 45
        max_duration = self.config.get('douyin_video.max_duration', 80) if self.config else 80
        min_likes = self.config.get('douyin_video.min_likes', 1000) if self.config else 1000
        download_count = self.config.get('douyin_video.download_count', 5) if self.config else 5
        scroll_times = self.config.get('douyin_video.scroll_times', 3) if self.config else 3

        self.log_signal.emit(f"抖音视频筛选条件:")
        self.log_signal.emit(f"  - 时长: {min_duration}s - {max_duration}s")
        self.log_signal.emit(f"  - 最低点赞: {min_likes}")
        self.log_signal.emit(f"  - 每个产品下载数量: {download_count}")
        self.log_signal.emit(f"  - 搜索滚动次数: {scroll_times}")

        # 创建抖音搜索器
        searcher = DouyinSearcher(browser_manager, self.account_id, self.config)
        self.log_signal.emit("\n正在打开抖音...")
        searcher.start()

        # 统计信息
        stats = {
            'total': len(products),
            'success': 0,
            'no_video_found': 0,
            'no_match': 0,
            'error': 0
        }

        for i, product in enumerate(products):
            try:
                self.log_signal.emit(f"\n{'='*60}")
                self.log_signal.emit(f"[{i+1}/{len(products)}] 搜索产品视频: {product.title[:40]}...")

                self.progress_signal.emit(f"搜索视频 {i+1}/{len(products)}", i+1, len(products))

                # 清理产品名称用于搜索 (移除特殊字符)
                search_keyword = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', product.title).strip()
                if not search_keyword:
                    self.log_signal.emit("  警告: 产品名称无法用于搜索")
                    continue

                # 构建抖音搜索URL
                encoded_keyword = urllib.parse.quote(search_keyword)
                search_url = f"https://www.douyin.com/search/{encoded_keyword}?type=video"
                self.log_signal.emit(f"  搜索: {search_keyword[:50]}...")

                # 搜索视频
                videos = searcher.search_by_url(
                    search_url,
                    scroll_times=scroll_times,
                    on_log=lambda msg: self.log_signal.emit(f"  {msg}")
                )

                if not videos:
                    self.log_signal.emit("  ⚠️ 警告: 搜索未找到任何视频!")
                    self.log_signal.emit(f"     搜索关键词: {search_keyword[:50]}")
                    stats['no_video_found'] += 1
                    continue

                self.log_signal.emit(f"  找到 {len(videos)} 个视频，开始筛选...")

                # 调试：显示前5个视频的数据
                self.log_signal.emit(f"  [调试] 前5个视频数据:")
                for idx, v in enumerate(videos[:5]):
                    self.log_signal.emit(f"    [{idx+1}] 时长={v.duration}s, 点赞={v.likes}, 标题={v.title[:30]}...")

                # 筛选视频
                self.log_signal.emit(f"  筛选条件: 时长 {min_duration}-{max_duration}s, 最低 {min_likes} 赞")

                # 检查是否大部分视频的点赞数都是0（数据获取问题）
                videos_with_likes = [v for v in videos if v.likes > 0]
                actual_min_likes = min_likes
                if len(videos_with_likes) < len(videos) * 0.1:  # 如果90%以上的视频点赞数都是0
                    self.log_signal.emit(f"  警告: 大部分视频点赞数为0，可能是数据获取问题，暂时忽略点赞筛选")
                    actual_min_likes = 0  # 忽略点赞条件

                filtered_videos = searcher.filter_videos(
                    videos,
                    min_duration=min_duration,
                    max_duration=max_duration,
                    min_likes=actual_min_likes,
                    top_n=download_count
                )

                if not filtered_videos:
                    self.log_signal.emit(f"  ⚠️ 警告: 筛选后无符合条件的视频!")
                    self.log_signal.emit(f"     筛选条件: 时长 {min_duration}-{max_duration}s, 最低 {actual_min_likes} 赞")
                    # 统计不符合原因
                    duration_short = sum(1 for v in videos if v.duration < min_duration)
                    duration_long = sum(1 for v in videos if v.duration > max_duration)
                    likes_fail = sum(1 for v in videos if v.likes < actual_min_likes)
                    self.log_signal.emit(f"     时长过短(<{min_duration}s): {duration_short} 个")
                    self.log_signal.emit(f"     时长过长(>{max_duration}s): {duration_long} 个")
                    if actual_min_likes > 0:
                        self.log_signal.emit(f"     点赞不足(<{actual_min_likes}): {likes_fail} 个")
                    stats['no_match'] += 1
                    continue

                self.log_signal.emit(f"  筛选出 {len(filtered_videos)} 个符合条件的视频:")
                for j, v in enumerate(filtered_videos):
                    self.log_signal.emit(f"    [{j+1}] {v.duration:.0f}s, {v.likes}赞, {v.title[:30]}...")

                # 获取视频下载URL
                self.log_signal.emit("  获取视频下载链接...")
                for v in filtered_videos:
                    if not v.download_url:
                        searcher.get_video_download_url(v)

                # 确定输出目录 (与产品素材同目录)
                product_dir = self._get_product_dir(output_dir, product)

                # 下载视频
                self.log_signal.emit(f"  开始下载视频到: {product_dir}")
                downloader = VideoDownloader(product_dir)

                downloaded_videos = downloader.download_videos(
                    filtered_videos,
                    on_progress=lambda msg, cur, total: self.progress_signal.emit(f"下载视频 {cur}/{total}", cur, total),
                    on_log=lambda msg: self.log_signal.emit(f"  {msg}")
                )

                self.log_signal.emit(f"  下载完成: {len(downloaded_videos)}/{len(filtered_videos)} 个视频")

                # 更新产品信息 JSON，添加下载的视频信息
                self._update_product_info_with_videos(product_dir, downloaded_videos)

                if downloaded_videos:
                    stats['success'] += 1

            except Exception as e:
                import traceback
                self.log_signal.emit(f"  处理产品时出错: {e}")
                traceback.print_exc()
                stats['error'] += 1

        # 关闭抖音浏览器
        self.log_signal.emit("\n关闭抖音浏览器...")
        searcher.close()

        # 输出汇总统计
        self.log_signal.emit("\n" + "=" * 60)
        self.log_signal.emit("抖音视频搜索汇总:")
        self.log_signal.emit("=" * 60)
        self.log_signal.emit(f"  总产品数: {stats['total']}")
        self.log_signal.emit(f"  ✓ 成功下载视频: {stats['success']} 个产品")
        if stats['no_video_found'] > 0:
            self.log_signal.emit(f"  ✗ 搜索无结果: {stats['no_video_found']} 个产品")
        if stats['no_match'] > 0:
            self.log_signal.emit(f"  ✗ 无匹配视频: {stats['no_match']} 个产品 (时长/点赞不符)")
        if stats['error'] > 0:
            self.log_signal.emit(f"  ✗ 处理出错: {stats['error']} 个产品")
        self.log_signal.emit("=" * 60)

    def _get_product_dir(self, output_dir: Path, product) -> Path:
        """获取产品目录路径"""
        import re
        # 清理产品标题
        title_clean = re.sub(r'[<>:"/\\|?*]', '_', product.title[:20])
        dir_name = f"{product.product_id}_{title_clean}"
        return output_dir / dir_name

    def _update_product_info_with_videos(self, product_dir: Path, videos):
        """更新产品信息 JSON，添加下载的视频信息"""
        import json
        from datetime import datetime

        json_path = product_dir / "product_info.json"
        if not json_path.exists():
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                product_info = json.load(f)

            # 添加抖音视频信息
            product_info['douyin_videos'] = []
            for v in videos:
                product_info['douyin_videos'].append({
                    'video_id': v.video_id,
                    'title': v.title,
                    'url': v.url,
                    'duration': v.duration,
                    'likes': v.likes,
                    'comments': v.comments,
                    'shares': v.shares,
                    'author_name': v.author_name,
                    'local_path': v.local_path,
                    'download_url': v.download_url,
                })

            product_info['douyin_search_time'] = datetime.now().isoformat()

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(product_info, f, ensure_ascii=False, indent=2)

            self.log_signal.emit(f"  已更新产品信息: {json_path.name}")

        except Exception as e:
            self.log_signal.emit(f"  更新产品信息失败: {e}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.account_manager = AccountManager()
        self.pipeline = Pipeline(self.account_manager, self.config)
        self.worker = None
        self.test_worker = None
        self.browser_thread = None  # 浏览器操作线程
        self.profile_thread = None  # Profile 导入/导出线程
        self.picking_thread = None  # 选品线程
        self._login_buttons = {}  # 保存登录按钮引用

        self.init_ui()
        self.load_accounts()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("抖音自动化营销工具")
        self.setMinimumSize(1000, 700)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧面板 (控制区)
        left_panel = self.create_left_panel()
        left_panel.setMaximumWidth(350)

        # 右侧面板 (日志区)
        right_panel = self.create_right_panel()

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])

        main_layout.addWidget(splitter)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏
        self.statusBar().showMessage("就绪")

    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 账户选择
        account_group = QGroupBox("账户管理")
        account_layout = QVBoxLayout(account_group)

        account_row = QHBoxLayout()
        account_row.addWidget(QLabel("选择账户:"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(150)
        account_row.addWidget(self.account_combo)

        btn_add_account = QPushButton("添加")
        btn_add_account.clicked.connect(self.add_account)
        account_row.addWidget(btn_add_account)

        account_layout.addLayout(account_row)

        # 账户登录按钮
        login_row = QHBoxLayout()
        btn_login_baiying = QPushButton("登录百应")
        btn_login_baiying.clicked.connect(lambda: self.login_platform('baiying'))
        btn_login_douyin = QPushButton("登录抖音")
        btn_login_douyin.clicked.connect(lambda: self.login_platform('douyin'))
        btn_login_creator = QPushButton("登录创作者")
        btn_login_creator.clicked.connect(lambda: self.login_platform('douyin_creator'))
        login_row.addWidget(btn_login_baiying)
        login_row.addWidget(btn_login_douyin)
        login_row.addWidget(btn_login_creator)
        account_layout.addLayout(login_row)

        # 保存按钮引用，用于启用/禁用
        self._login_buttons = {
            'baiying': btn_login_baiying,
            'douyin': btn_login_douyin,
            'douyin_creator': btn_login_creator
        }

        layout.addWidget(account_group)

        # 任务设置
        task_group = QGroupBox("任务设置")
        task_layout = QVBoxLayout(task_group)

        # 说明文字
        task_desc = QLabel("点击「开始选品」打开百应平台进行智能选品")
        task_desc.setStyleSheet("color: #666; font-size: 12px;")
        task_layout.addWidget(task_desc)

        # 产品 URL 输入 (可选，手动指定)
        url_layout = QFormLayout()
        self.product_url_input = QLineEdit()
        self.product_url_input.setPlaceholderText("可选：手动输入百应产品URL")
        url_layout.addRow("产品URL:", self.product_url_input)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("可选，留空自动生成")
        url_layout.addRow("项目名称:", self.project_name_input)
        task_layout.addLayout(url_layout)

        layout.addWidget(task_group)

        # 进度显示
        progress_group = QGroupBox("任务进度")
        progress_layout = QVBoxLayout(progress_group)

        self.status_label = QLabel("状态: 等待开始")
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.step_label = QLabel("步骤: -")
        progress_layout.addWidget(self.step_label)

        layout.addWidget(progress_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("开始选品")
        self.btn_start.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.btn_start.clicked.connect(self.start_picking)
        btn_layout.addWidget(self.btn_start)

        self.btn_run_url = QPushButton("运行URL")
        self.btn_run_url.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 10px; }")
        self.btn_run_url.clicked.connect(self.start_task_with_url)
        self.btn_run_url.setToolTip("使用输入的产品URL直接运行任务")
        btn_layout.addWidget(self.btn_run_url)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_task)
        btn_layout.addWidget(self.btn_stop)

        layout.addLayout(btn_layout)

        # 测试按钮
        test_row = QHBoxLayout()
        btn_test = QPushButton("测试剪映→上传")
        btn_test.clicked.connect(self.start_test_jianying_upload)
        test_row.addWidget(btn_test)

        btn_upload_test = QPushButton("测试上传")
        btn_upload_test.clicked.connect(self.start_test_upload_only)
        test_row.addWidget(btn_upload_test)

        layout.addLayout(test_row)

        # 设置按钮
        btn_settings = QPushButton("设置")
        btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(btn_settings)

        layout.addStretch()

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧日志面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 日志标签
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("运行日志"))
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self.clear_log)
        log_header.addWidget(btn_clear)
        log_header.addStretch()
        layout.addLayout(log_header)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #d4d4d4; }")
        layout.addWidget(self.log_text)

        return panel

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        action_settings = QAction("设置", self)
        action_settings.triggered.connect(self.open_settings)
        file_menu.addAction(action_settings)

        file_menu.addSeparator()

        action_exit = QAction("退出", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # 账户菜单
        account_menu = menubar.addMenu("账户")

        action_add = QAction("添加账户", self)
        action_add.triggered.connect(self.add_account)
        account_menu.addAction(action_add)

        action_delete = QAction("删除账户", self)
        action_delete.triggered.connect(self.delete_account)
        account_menu.addAction(action_delete)

        account_menu.addSeparator()

        action_export = QAction("导出 Profile...", self)
        action_export.triggered.connect(self.export_profile)
        account_menu.addAction(action_export)

        action_import = QAction("导入 Profile...", self)
        action_import.triggered.connect(self.import_profile)
        account_menu.addAction(action_import)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        action_about = QAction("关于", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    def load_accounts(self):
        """加载账户列表"""
        self.account_combo.clear()
        accounts = self.account_manager.list_accounts()
        for acc in accounts:
            self.account_combo.addItem(f"{acc.name} ({acc.account_id})", acc.account_id)

        if not accounts:
            self.account_combo.addItem("无账户 - 请先添加", None)

    def load_settings(self):
        """从配置重新加载设置（设置对话框保存后调用）"""
        # 配置已由 SettingsDialog 保存，这里只需要重新加载
        # 主窗口不再显示设置输入框，所以无需更新 UI
        pass

    def add_account(self):
        """添加账户"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "添加账户", "请输入账户名称:")
        if ok and name:
            try:
                account = self.account_manager.create_account(name)
                self.load_accounts()
                # 选择新创建的账户
                index = self.account_combo.findData(account.account_id)
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)
                self.log(f"账户已创建: {account.account_id}")
                QMessageBox.information(self, "成功", f"账户 '{name}' 创建成功!")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"创建账户失败: {e}")

    def delete_account(self):
        """删除账户"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除账户 '{account_id}' 吗?\n这将删除所有相关数据!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.account_manager.delete_account(account_id, delete_data=True)
            self.load_accounts()
            self.log(f"账户已删除: {account_id}")

    def login_platform(self, platform: str):
        """打开浏览器登录平台 (异步)"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        # 如果已有浏览器线程在运行，不重复启动
        if self.browser_thread and self.browser_thread.isRunning():
            self.log("浏览器正在启动中，请稍候...")
            return

        platform_names = {
            'baiying': '百应',
            'douyin': '抖音',
            'douyin_creator': '抖音创作者中心'
        }

        # 禁用当前登录按钮
        if platform in self._login_buttons:
            self._login_buttons[platform].setEnabled(False)
            self._login_buttons[platform].setText("启动中...")

        self.statusBar().showMessage(f"正在启动浏览器...")

        # 在后台线程中启动浏览器
        self.browser_thread = BrowserThread(self.account_manager, account_id, platform)
        self.browser_thread.log_signal.connect(self.log)
        self.browser_thread.finished_signal.connect(
            lambda success, msg: self._on_browser_finished(platform, success, msg)
        )
        self.browser_thread.start()

    def _on_browser_finished(self, platform: str, success: bool, message: str):
        """浏览器启动完成回调"""
        button_texts = {
            'baiying': '登录百应',
            'douyin': '登录抖音',
            'douyin_creator': '登录创作者'
        }

        # 恢复按钮状态
        if platform in self._login_buttons:
            self._login_buttons[platform].setEnabled(True)
            self._login_buttons[platform].setText(button_texts[platform])

        platform_names = {
            'baiying': '百应',
            'douyin': '抖音',
            'douyin_creator': '抖音创作者中心'
        }

        if success:
            self.log(f"✓ {message}")
            self.statusBar().showMessage(f"请在浏览器中登录 {platform_names[platform]}")
        else:
            self.log(f"✗ {message}")
            self.statusBar().showMessage("浏览器启动失败")
            QMessageBox.warning(self, "错误", message)

    def start_picking(self):
        """开始选品 - 打开百应，登录后自动进入选品页面并应用筛选"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        # 如果已有选品线程在运行
        if self.picking_thread and self.picking_thread.isRunning():
            self.log("正在打开选品页面，请稍候...")
            return

        # 禁用开始按钮
        self.btn_start.setEnabled(False)
        self.btn_start.setText("选品中...")
        self.statusBar().showMessage("正在启动百应选品...")

        # 显示筛选配置
        filter_config = self.config.get('filter', {})
        picking_config = self.config.get('picking', {})
        product_count = picking_config.get('product_count', 3)

        self.log("=" * 50)
        self.log("开始智能选品")
        self.log(f"账户: {account_id}")
        self.log(f"目标产品数量: {product_count}")
        self.log(f"筛选配置:")
        self.log(f"  - 月销量: >= {filter_config.get('monthly_sales_min', 0)}")
        self.log(f"  - 好评率: >= {filter_config.get('min_rating', 0)}%")
        self.log(f"  - 价格范围: ¥{filter_config.get('price_min', 0)} - ¥{filter_config.get('price_max', 9999)}")
        self.log(f"  - 佣金范围: ¥{filter_config.get('commission_min', 0)} - ¥{filter_config.get('commission_max', 9999)}")
        self.log("=" * 50)

        # 在后台线程中打开百应，传入 config 用于筛选
        self.picking_thread = PickingThread(self.account_manager, account_id, self.config)
        self.picking_thread.log_signal.connect(self.log)
        self.picking_thread.progress_signal.connect(self.update_progress)
        self.picking_thread.finished_signal.connect(self._on_picking_finished)
        self.picking_thread.start()

    def _on_picking_finished(self, success: bool, message: str):
        """选品流程完成回调"""
        self.btn_start.setEnabled(True)
        self.btn_start.setText("开始选品")

        if success:
            self.log(f"\n✓ {message}")
            self.statusBar().showMessage("选品完成")
            QMessageBox.information(self, "选品完成", message)
        else:
            self.log(f"\n✗ {message}")
            self.statusBar().showMessage("选品流程失败")
            QMessageBox.warning(self, "选品失败", message)

    def start_task_with_url(self):
        """使用 URL 开始任务"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        product_url = self.product_url_input.text().strip()
        if not product_url:
            QMessageBox.warning(self, "警告", "请输入产品URL")
            return

        project_name = self.project_name_input.text().strip() or None

        # 禁用按钮
        self.btn_start.setEnabled(False)
        self.btn_run_url.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("状态: 正在启动...")

        self.log("=" * 50)
        self.log("开始自动化任务")
        self.log(f"账户: {account_id}")
        self.log(f"产品URL: {product_url}")
        self.log("=" * 50)

        # 创建新的 Pipeline 实例
        self.pipeline = Pipeline(self.account_manager, self.config)

        # 创建工作线程
        self.worker = WorkerThread(self.pipeline, account_id, product_url, project_name)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.task_finished)
        self.worker.start()

    def stop_task(self):
        """停止任务"""
        if self.pipeline:
            self.pipeline.stop()
        self.log("正在停止任务...")
        self.statusBar().showMessage("正在停止...")

    def start_test_jianying_upload(self):
        """测试从剪映生成到上传的流程"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        asset_dir = Path(TEST_ASSET_DIR)
        if not asset_dir.exists():
            QMessageBox.warning(self, "错误", f"测试素材目录不存在:\n{asset_dir}")
            return

        video_exts = {'.mp4', '.mov', '.mkv'}
        image_exts = {'.jpg', '.jpeg', '.png', '.webp'}

        video_paths = [p for p in asset_dir.iterdir() if p.is_file() and p.suffix.lower() in video_exts]
        image_paths = [p for p in asset_dir.iterdir() if p.is_file() and p.suffix.lower() in image_exts]

        if not video_paths:
            QMessageBox.warning(self, "错误", "测试素材目录中未找到视频文件")
            return
        if not image_paths:
            QMessageBox.warning(self, "错误", "测试素材目录中未找到图片文件")
            return

        self.btn_start.setEnabled(False)
        self.btn_run_url.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("状态: 正在启动...")

        self.log("=" * 50)
        self.log("开始测试流程: 剪映 → 导出 → 上传")
        self.log(f"账户: {account_id}")
        self.log("=" * 50)

        self.pipeline = Pipeline(self.account_manager, self.config)
        self.test_worker = JianyingUploadThread(
            self.pipeline, account_id, video_paths, image_paths, project_name="test_jianying_upload"
        )
        self.test_worker.log_signal.connect(self.log)
        self.test_worker.progress_signal.connect(self.update_progress)
        self.test_worker.status_signal.connect(self.update_status)
        self.test_worker.finished_signal.connect(self.task_finished)
        self.test_worker.start()

    def start_test_upload_only(self):
        """测试仅上传视频"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要上传的视频", "", "视频文件 (*.mp4 *.mov *.mkv)"
        )
        if not file_path:
            return

        cover_paths = []
        asset_dir = Path(TEST_ASSET_DIR)
        if asset_dir.exists():
            image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
            cover_paths = [
                str(p) for p in asset_dir.iterdir()
                if p.is_file() and p.suffix.lower() in image_exts
            ]

        self.btn_start.setEnabled(False)
        self.btn_run_url.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("状态: 正在启动...")

        self.log("=" * 50)
        self.log("开始测试流程: 仅上传")
        self.log(f"账户: {account_id}")
        self.log(f"视频: {file_path}")
        self.log("=" * 50)

        self.upload_worker = UploadOnlyThread(
            self.account_manager, self.config, account_id, file_path, cover_paths
        )
        self.upload_worker.log_signal.connect(self.log)
        self.upload_worker.finished_signal.connect(self.task_finished)
        self.upload_worker.start()

    def task_finished(self, success: bool, message: str):
        """任务完成回调"""
        self.btn_start.setEnabled(True)
        self.btn_run_url.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("状态: 完成")
            self.log(f"✓ {message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.status_label.setText("状态: 失败")
            self.log(f"✗ {message}")
            QMessageBox.warning(self, "失败", message)

        self.statusBar().showMessage("就绪")

    def update_progress(self, step: str, current: int, total: int):
        """更新进度"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        self.step_label.setText(f"步骤: {step} ({current}/{total})")

    def update_status(self, status: str):
        """更新状态"""
        status_names = {
            'pending': '等待',
            'product_searching': '搜索产品',
            'product_found': '产品已找到',
            'material_downloading': '下载素材',
            'material_downloaded': '素材已下载',
            'video_searching': '搜索视频',
            'video_filtered': '视频已筛选',
            'video_downloading': '下载视频',
            'video_downloaded': '视频已下载',
            'jianying_generating': '生成剪映项目',
            'jianying_generated': '剪映项目已生成',
            'exporting': '导出视频',
            'exported': '视频已导出',
            'uploading': '上传视频',
            'published': '已发布',
            'completed': '完成',
            'failed': '失败',
        }
        status_text = status_names.get(status, status)
        self.status_label.setText(f"状态: {status_text}")
        self.statusBar().showMessage(f"当前: {status_text}")

    def log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def open_settings(self):
        """打开设置对话框"""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.load_settings()
            self.log("设置已更新")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "抖音自动化营销工具 v1.0\n\n"
            "功能:\n"
            "• 百应选品\n"
            "• 抖音视频搜索下载\n"
            "• 剪映自动剪辑导出\n"
            "• 抖音自动上传发布\n\n"
            "多账户支持 | 断点恢复 | AI文案生成"
        )

    def export_profile(self):
        """导出 Profile (异步)"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        # 如果已有线程在运行
        if self.profile_thread and self.profile_thread.isRunning():
            self.log("正在处理中，请稍候...")
            return

        # 选择平台
        platforms = ['baiying', 'douyin', 'douyin_creator']
        platform_names = ['百应', '抖音', '抖音创作者中心']

        from PyQt6.QtWidgets import QInputDialog
        platform_name, ok = QInputDialog.getItem(
            self, "选择平台",
            "请选择要导出的平台:",
            platform_names, 0, False
        )

        if not ok:
            return

        platform = platforms[platform_names.index(platform_name)]

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 Profile",
            f"profile_{account_id}_{platform}",
            "ZIP 文件 (*.zip)"
        )

        if not file_path:
            return

        # 在后台线程中执行导出
        self.statusBar().showMessage("正在导出 Profile...")
        self.profile_thread = ProfileExportThread(
            self.account_manager, account_id, platform, file_path
        )
        self.profile_thread.log_signal.connect(self.log)
        self.profile_thread.finished_signal.connect(self._on_export_finished)
        self.profile_thread.start()

    def _on_export_finished(self, success: bool, message: str):
        """导出完成回调"""
        if success:
            self.log(f"✓ Profile 已导出: {message}")
            self.statusBar().showMessage("导出完成")
            QMessageBox.information(self, "导出成功", f"Profile 已导出到:\n{message}")
        else:
            self.log(f"✗ {message}")
            self.statusBar().showMessage("导出失败")
            QMessageBox.warning(self, "导出失败", message)

    def import_profile(self):
        """导入 Profile (异步)"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        # 如果已有线程在运行
        if self.profile_thread and self.profile_thread.isRunning():
            self.log("正在处理中，请稍候...")
            return

        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入 Profile",
            "",
            "ZIP 文件 (*.zip)"
        )

        if not file_path:
            return

        # 选择目标平台
        platforms = ['baiying', 'douyin', 'douyin_creator']
        platform_names = ['百应', '抖音', '抖音创作者中心']

        from PyQt6.QtWidgets import QInputDialog
        platform_name, ok = QInputDialog.getItem(
            self, "选择目标平台",
            "请选择要导入到的平台:",
            platform_names, 0, False
        )

        if not ok:
            return

        platform = platforms[platform_names.index(platform_name)]

        # 确认覆盖
        reply = QMessageBox.question(
            self, "确认导入",
            f"导入将覆盖 {platform_name} 的现有登录数据。\n确定要继续吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 在后台线程中执行导入
        self.statusBar().showMessage("正在导入 Profile...")
        self.profile_thread = ProfileImportThread(
            self.account_manager, account_id, platform, file_path
        )
        self.profile_thread.log_signal.connect(self.log)
        self.profile_thread.finished_signal.connect(self._on_import_finished)
        self.profile_thread.start()

    def _on_import_finished(self, success: bool, message: str):
        """导入完成回调"""
        if success:
            self.log(f"✓ {message}")
            self.statusBar().showMessage("导入完成")
            QMessageBox.information(self, "导入成功", message)
        else:
            self.log(f"✗ {message}")
            self.statusBar().showMessage("导入失败")
            QMessageBox.warning(self, "导入失败", message)

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "任务正在运行中，确定要退出吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self.pipeline.stop()
            self.worker.wait(3000)

        event.accept()


def run_app():
    """运行应用"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    run_app()
