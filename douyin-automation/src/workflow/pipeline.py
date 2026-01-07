"""工作流管道

串联所有步骤: 百应选品 → 素材下载 → 抖音搜索 → 视频下载 → 剪映剪辑 → 导出 → 上传
"""

import uuid
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

from core.account_manager import AccountManager
from core.browser_manager import BrowserManager
from core.config import Config
from models.project import Project, ProjectStatus
from models.product import Product
from models.video import Video, ExportedVideo
from platforms.baiying import BaiyingPicker
from platforms.douyin import DouyinSearcher, VideoDownloader, DouyinUploader
from platforms.jianying import JianyingGenerator, JianyingExporter
from workflow.checkpoint import Checkpoint


class Pipeline:
    """工作流管道

    管理从选品到上传的完整流程
    """

    def __init__(
        self,
        account_manager: AccountManager,
        config: Optional[Config] = None
    ):
        """初始化管道

        Args:
            account_manager: 账户管理器
            config: 配置对象
        """
        self.account_manager = account_manager
        self.config = config or Config()
        self.browser_manager = BrowserManager(account_manager)
        self.checkpoint = Checkpoint()

        # 回调函数
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_progress: Optional[Callable[[str, int, int], None]] = None
        self.on_status_change: Optional[Callable[[Project], None]] = None

        # 当前项目
        self.current_project: Optional[Project] = None
        self._is_running = False
        self._should_stop = False

    def log(self, message: str) -> None:
        """记录日志"""
        if self.on_log:
            self.on_log(message)
        print(f"[Pipeline] {message}")

        if self.current_project:
            self.current_project.add_log(message)

    def update_progress(self, step: str, current: int, total: int) -> None:
        """更新进度"""
        if self.on_progress:
            self.on_progress(step, current, total)

    def update_status(self, status: ProjectStatus, step: str = "") -> None:
        """更新状态"""
        if self.current_project:
            self.current_project.update_status(status, step)
            self.checkpoint.auto_save(self.current_project)

            if self.on_status_change:
                self.on_status_change(self.current_project)

    def stop(self) -> None:
        """停止管道"""
        self._should_stop = True
        self.log("正在停止...")

    def run(
        self,
        account_id: str,
        product_url: Optional[str] = None,
        product: Optional[Product] = None,
        project_name: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> Optional[Project]:
        """运行完整工作流

        Args:
            account_id: 账户ID
            product_url: 产品URL (与product二选一)
            product: 产品对象 (与product_url二选一)
            project_name: 项目名称
            output_dir: 输出目录

        Returns:
            完成的Project对象
        """
        if self._is_running:
            self.log("已有任务正在运行")
            return None

        self._is_running = True
        self._should_stop = False

        try:
            # 创建项目
            project_id = str(uuid.uuid4())
            project_name = project_name or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if output_dir is None:
                output_dir = Path(self.config.get('output.base_dir', '')) or Path.cwd() / "output"

            project_dir = output_dir / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            self.current_project = Project(
                project_id=project_id,
                name=project_name,
                account_id=account_id,
                project_dir=str(project_dir)
            )

            self.log(f"开始项目: {project_name}")
            self.log(f"账户: {account_id}")

            # 步骤1: 获取产品信息
            if not self._should_stop:
                if product:
                    self.current_project.set_product(product)
                    self.update_status(ProjectStatus.PRODUCT_FOUND, "使用提供的产品信息")
                elif product_url:
                    product = self._step_product_search(account_id, product_url, project_dir)
                    if not product:
                        raise Exception("获取产品信息失败")
                    self.current_project.set_product(product)
                else:
                    raise ValueError("必须提供product_url或product参数")

            # 步骤2: 下载素材
            if not self._should_stop:
                product = self._step_material_download(product, project_dir)

            # 步骤3: 抖音视频搜索
            if not self._should_stop:
                videos = self._step_video_search(account_id, product)

            # 步骤4: 下载视频
            if not self._should_stop:
                videos = self._step_video_download(videos, project_dir / "videos")

            # 步骤5: 生成剪映项目
            if not self._should_stop:
                draft_path = self._step_jianying_generate(videos, project_name, project_dir)

            # 步骤6: 导出视频
            if not self._should_stop:
                exported = self._step_jianying_export(draft_path, project_dir)

            # 步骤7: 上传到抖音
            if not self._should_stop:
                self._step_douyin_upload(account_id, exported, product)

            # 完成
            self.current_project.mark_completed()
            self.checkpoint.save(self.current_project)
            self.log("项目完成!")

            return self.current_project

        except Exception as e:
            self.log(f"项目失败: {e}")
            if self.current_project:
                self.current_project.mark_failed(str(e))
                self.checkpoint.save(self.current_project)
            return self.current_project

        finally:
            self._is_running = False
            self._close_browsers()

    def run_from_videos(
        self,
        account_id: str,
        video_paths: List[Path],
        image_paths: Optional[List[Path]] = None,
        project_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
        product: Optional[Product] = None
    ) -> Optional[Project]:
        """从本地视频开始执行：剪映生成 -> 导出 -> 抖音上传"""
        if self._is_running:
            self.log("已有任务正在运行")
            return None

        self._is_running = True
        self._should_stop = False

        try:
            project_id = str(uuid.uuid4())
            project_name = project_name or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if output_dir is None:
                output_dir = Path(self.config.get('output.base_dir', '')) or Path.cwd() / "output"

            project_dir = output_dir / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            self.current_project = Project(
                project_id=project_id,
                name=project_name,
                account_id=account_id,
                project_dir=str(project_dir)
            )

            if product is None:
                product = Product(
                    product_id="test_product",
                    title="测试产品",
                    url="",
                    price=0.0,
                    commission=0.0
                )
            self.current_project.set_product(product)

            videos: List[Video] = []
            for i, path in enumerate(video_paths, start=1):
                p = Path(path)
                if not p.exists():
                    raise FileNotFoundError(f"视频不存在: {p}")
                videos.append(Video(
                    video_id=f"local_{i}",
                    title=p.stem,
                    url="",
                    local_path=str(p)
                ))

            images: List[str] = []
            if image_paths:
                for path in image_paths:
                    p = Path(path)
                    if not p.exists():
                        raise FileNotFoundError(f"图片不存在: {p}")
                    images.append(str(p))

            if not self._should_stop:
                draft_path = self._step_jianying_generate(videos, project_name, project_dir, image_paths=images)

            if not self._should_stop:
                exported = self._step_jianying_export(draft_path, project_dir)

            if not self._should_stop:
                self._step_douyin_upload(account_id, exported, product)

            self.current_project.mark_completed()
            self.checkpoint.save(self.current_project)
            self.log("项目完成!")

            return self.current_project

        except Exception as e:
            self.log(f"项目失败: {e}")
            if self.current_project:
                self.current_project.mark_failed(str(e))
                self.checkpoint.save(self.current_project)
            return self.current_project

        finally:
            self._is_running = False
            self._close_browsers()

    def resume(self, project_id: str) -> Optional[Project]:
        """恢复项目

        Args:
            project_id: 项目ID

        Returns:
            完成的Project对象
        """
        project = self.checkpoint.load(project_id)
        if not project:
            self.log(f"未找到项目: {project_id}")
            return None

        if project.is_finished:
            self.log(f"项目已结束: {project.status}")
            return project

        self.current_project = project
        resume_step = self.checkpoint.get_resume_step(project)
        self.log(f"从步骤恢复: {resume_step}")

        # 根据步骤恢复执行
        # TODO: 实现具体的恢复逻辑

        return project

    def _step_product_search(
        self,
        account_id: str,
        product_url: str,
        output_dir: Path
    ) -> Optional[Product]:
        """步骤1: 百应产品搜索"""
        self.update_status(ProjectStatus.PRODUCT_SEARCHING, "搜索产品")
        self.update_progress("搜索产品", 1, 7)
        self.log(f"访问产品页面: {product_url}")

        picker = BaiyingPicker(self.browser_manager, account_id, self.config)
        try:
            picker.start()

            # 检查登录
            if not picker.is_logged_in():
                self.log("请在浏览器中登录百应...")
                if not picker.wait_for_login():
                    raise Exception("登录超时")

            product = picker.process_product_url(
                product_url,
                output_dir / "materials",
                on_log=self.log
            )

            if product:
                self.update_status(ProjectStatus.PRODUCT_FOUND, "产品信息获取成功")
                self.log(f"产品: {product.title}")
                self.log(f"价格: ¥{product.price}, 佣金: ¥{product.commission}")

                self.current_project.search_results_count = 1
                self.current_project.filtered_results_count = 1

            return product

        finally:
            picker.close()

    def _step_material_download(
        self,
        product: Product,
        output_dir: Path
    ) -> Product:
        """步骤2: 下载产品素材"""
        self.update_status(ProjectStatus.MATERIAL_DOWNLOADING, "下载素材")
        self.update_progress("下载素材", 2, 7)

        if product.materials_downloaded:
            self.log("素材已下载，跳过")
            self.update_status(ProjectStatus.MATERIAL_DOWNLOADED)
            return product

        from platforms.baiying import MaterialDownloader
        downloader = MaterialDownloader(output_dir / "materials")
        product = downloader.download_materials(
            product,
            on_progress=lambda msg, cur, total: self.log(f"  {msg}")
        )

        self.log(f"下载完成: {len(product.local_images)} 张图片")
        self.update_status(ProjectStatus.MATERIAL_DOWNLOADED, "素材下载完成")

        return product

    def _step_video_search(
        self,
        account_id: str,
        product: Product
    ) -> List[Video]:
        """步骤3: 抖音视频搜索"""
        self.update_status(ProjectStatus.VIDEO_SEARCHING, "搜索视频")
        self.update_progress("搜索视频", 3, 7)

        # 使用产品标题搜索
        keyword = product.title[:20]
        self.log(f"搜索关键词: {keyword}")

        searcher = DouyinSearcher(self.browser_manager, account_id, self.config)
        try:
            searcher.start()
            videos = searcher.search_videos(keyword, scroll_times=5, on_log=self.log)

            self.log(f"搜索结果: {len(videos)} 个视频")
            self.current_project.search_results_count = len(videos)

            # 筛选
            video_config = self.config.get('douyin_video', {})
            filtered = searcher.filter_videos(
                videos,
                min_duration=video_config.get('min_duration', 45),
                max_duration=video_config.get('max_duration', 80),
                min_likes=video_config.get('min_likes', 1000),
                top_n=video_config.get('download_count', 5)
            )

            self.log(f"筛选后: {len(filtered)} 个视频")
            self.current_project.filtered_results_count = len(filtered)
            self.update_status(ProjectStatus.VIDEO_FILTERED, "视频筛选完成")

            # 获取下载URL
            for video in filtered:
                if not video.download_url:
                    url = searcher.get_video_download_url(video)
                    video.download_url = url
                self.current_project.add_video(video)

            return filtered

        finally:
            searcher.close()

    def _step_video_download(
        self,
        videos: List[Video],
        output_dir: Path
    ) -> List[Video]:
        """步骤4: 下载视频"""
        self.update_status(ProjectStatus.VIDEO_DOWNLOADING, "下载视频")
        self.update_progress("下载视频", 4, 7)

        downloader = VideoDownloader(output_dir)
        downloaded = downloader.download_videos(
            videos,
            on_log=self.log,
            on_progress=lambda msg, cur, total: self.update_progress(msg, cur, total)
        )

        self.log(f"下载完成: {len(downloaded)} 个视频")
        self.current_project.downloaded_videos_count = len(downloaded)
        self.update_status(ProjectStatus.VIDEO_DOWNLOADED, "视频下载完成")

        return downloaded

    def _step_jianying_generate(
        self,
        videos: List[Video],
        project_name: str,
        output_dir: Path,
        image_paths: Optional[List[str]] = None
    ) -> str:
        """步骤5: 生成剪映项目"""
        self.update_status(ProjectStatus.JIANYING_GENERATING, "生成剪映项目")
        self.update_progress("生成剪映项目", 5, 7)

        template_path = self.config.get('jianying.template_dir', '')
        if not template_path:
            raise Exception("未配置剪映模板路径")

        generator = JianyingGenerator(template_path, config=self.config)
        draft_path = generator.generate_from_videos(
            videos,
            project_name,
            image_files=image_paths,
            on_log=self.log
        )

        self.current_project.jianying_draft_path = draft_path
        self.current_project.jianying_draft_name = project_name
        self.update_status(ProjectStatus.JIANYING_GENERATED, "剪映项目生成完成")
        self.log(f"剪映项目: {draft_path}")

        return draft_path

    def _step_jianying_export(
        self,
        draft_path: str,
        output_dir: Path
    ) -> ExportedVideo:
        """步骤6: 导出视频"""
        self.update_status(ProjectStatus.EXPORTING, "导出视频")
        self.update_progress("导出视频", 6, 7)

        exporter = JianyingExporter(self.config)
        export_dir = Path(self.config.get('jianying.export_dir', '') or output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(export_dir / "export.mp4")

        exported = exporter.export_draft(
            draft_path,
            output_path,
            on_log=self.log
        )

        if not exported:
            raise Exception("导出失败")

        self.current_project.set_exported_video(exported)
        self.update_status(ProjectStatus.EXPORTED, "视频导出完成")
        self.log(f"导出完成: {output_path}")

        return exported

    def _step_douyin_upload(
        self,
        account_id: str,
        video: ExportedVideo,
        product: Product
    ) -> None:
        """步骤7: 上传到抖音"""
        self.update_status(ProjectStatus.UPLOADING, "上传视频")
        self.update_progress("上传视频", 7, 7)

        # 生成发布信息（暂时硬编码）
        video.title = "测试标题"
        video.description = "测试描述"
        video.tags = self._generate_tags(product)

        uploader = DouyinUploader(self.browser_manager, account_id, self.config)
        try:
            uploader.start()

            if not uploader.is_logged_in():
                self.log("请在浏览器中登录抖音创作者中心...")
                if not uploader.wait_for_login():
                    raise Exception("登录超时")

            cover_paths = product.local_images if product else []
            if not cover_paths:
                asset_dir = Path(r"C:\Users\21346\OneDrive\桌面\jianying_test")
                if asset_dir.exists():
                    image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
                    candidates = [
                        str(p) for p in asset_dir.iterdir()
                        if p.is_file() and p.suffix.lower() in image_exts
                    ]
                    if candidates:
                        choice = random.choice(candidates)
                        cover_paths = [choice, choice]
            success = uploader.upload_video(video, cover_paths=cover_paths, on_log=self.log)

            if success:
                self.update_status(ProjectStatus.PUBLISHED, "视频发布成功")
                self.log("视频发布成功!")
            else:
                raise Exception("上传失败")

        finally:
            uploader.close()

    def _generate_tags(self, product: Product) -> List[str]:
        """生成视频标签"""
        # 简单实现，可以后续接入AI
        tags = ["好物推荐", "种草"]

        # 从标题提取关键词
        title_words = product.title.split()
        for word in title_words[:3]:
            if len(word) > 1:
                tags.append(word)

        return tags[:5]

    def _close_browsers(self) -> None:
        """关闭所有浏览器"""
        try:
            self.browser_manager.close_all_browsers()
        except Exception:
            pass
