"""抖音视频上传器

实现视频上传到抖音创作者中心
"""

import time
from pathlib import Path
from typing import Optional, Callable, List
from DrissionPage import ChromiumPage

from core.browser_manager import BrowserManager
from core.config import Config
from models.video import ExportedVideo


class DouyinUploader:
    """抖音视频上传器"""

    CREATOR_URL = "https://creator.douyin.com/creator-micro/content/upload"

    def __init__(
        self,
        browser_manager: BrowserManager,
        account_id: str,
        config: Optional[Config] = None
    ):
        """初始化上传器

        Args:
            browser_manager: 浏览器管理器
            account_id: 账户ID
            config: 配置对象
        """
        self.browser_manager = browser_manager
        self.account_id = account_id
        self.config = config or Config()
        self.page: Optional[ChromiumPage] = None

    def start(self, headless: bool = False) -> None:
        """启动浏览器"""
        self.page = self.browser_manager.navigate_to_platform(
            self.account_id, 'douyin_creator', headless
        )

    def close(self) -> None:
        """关闭浏览器"""
        self.browser_manager.close_browser(self.account_id, 'douyin_creator')
        self.page = None

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.browser_manager.is_logged_in(self.account_id, 'douyin_creator')

    def wait_for_login(self, timeout: float = 300) -> bool:
        """等待用户登录

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否登录成功
        """
        return self.browser_manager.wait_for_login(
            self.account_id, 'douyin_creator', timeout
        )

    def upload_video(
        self,
        video: ExportedVideo,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> bool:
        """上传视频

        Args:
            video: 导出的视频对象
            on_log: 日志回调
            on_progress: 进度回调

        Returns:
            是否成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        if not self.page:
            self.start()

        # 导航到上传页面
        log("打开抖音创作者中心...")
        self.page.get(self.CREATOR_URL)
        time.sleep(3)

        # 检查登录状态
        if not self.is_logged_in():
            log("未登录，请在浏览器中登录...")
            if not self.wait_for_login():
                log("登录超时")
                return False
            log("登录成功")

        if on_progress:
            on_progress("上传视频", 1, 5)

        # 查找上传按钮/区域
        try:
            upload_input = self._find_upload_input()
            if not upload_input:
                log("未找到上传入口")
                return False

            # 上传文件
            log(f"上传文件: {video.local_path}")
            upload_input.input(video.local_path)

            if on_progress:
                on_progress("等待上传完成", 2, 5)

            # 等待上传完成
            if not self._wait_for_upload_complete():
                log("上传超时")
                return False

            log("文件上传完成")

            if on_progress:
                on_progress("填写发布信息", 3, 5)

            # 填写标题
            if video.title:
                self._fill_title(video.title)
                log(f"标题: {video.title}")

            # 填写描述
            if video.description:
                self._fill_description(video.description)
                log(f"描述: {video.description[:50]}...")

            # 添加标签
            if video.tags:
                self._add_tags(video.tags)
                log(f"标签: {', '.join(video.tags)}")

            if on_progress:
                on_progress("发布视频", 4, 5)

            # 点击发布
            if not self._click_publish():
                log("发布失败")
                return False

            # 等待发布完成
            if not self._wait_for_publish_complete():
                log("发布超时")
                return False

            if on_progress:
                on_progress("发布成功", 5, 5)

            log("视频发布成功!")
            video.is_uploaded = True
            from datetime import datetime
            video.uploaded_at = datetime.now().isoformat()

            return True

        except Exception as e:
            log(f"上传失败: {e}")
            return False

    def _find_upload_input(self) -> Optional[object]:
        """查找上传输入框"""
        # 尝试多种选择器
        selectors = [
            'input[type="file"]',
            'input[accept*="video"]',
            '[class*="upload"] input',
            '[class*="Upload"] input',
        ]

        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=5)
                if ele:
                    return ele
            except Exception:
                pass

        return None

    def _wait_for_upload_complete(self, timeout: int = 600) -> bool:
        """等待上传完成

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否完成
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 检查进度条是否消失或显示100%
                progress = self.page.ele('[class*="progress"]', timeout=1)
                if not progress:
                    # 进度条消失，可能已完成
                    # 检查是否有错误
                    error = self.page.ele('[class*="error"]', timeout=0.5)
                    if error and error.text:
                        return False
                    return True

                # 检查进度文本
                progress_text = progress.text if progress else ""
                if '100%' in progress_text or '完成' in progress_text:
                    return True

            except Exception:
                pass

            time.sleep(2)

        return False

    def _fill_title(self, title: str) -> None:
        """填写标题"""
        selectors = [
            'textarea[placeholder*="标题"]',
            'input[placeholder*="标题"]',
            '[class*="title"] textarea',
            '[class*="title"] input',
        ]

        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.clear()
                    ele.input(title[:80])  # 限制长度
                    return
            except Exception:
                pass

    def _fill_description(self, description: str) -> None:
        """填写描述"""
        selectors = [
            'textarea[placeholder*="描述"]',
            'textarea[placeholder*="简介"]',
            '[class*="description"] textarea',
            '[class*="desc"] textarea',
        ]

        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.clear()
                    ele.input(description[:500])  # 限制长度
                    return
            except Exception:
                pass

    def _add_tags(self, tags: List[str]) -> None:
        """添加标签"""
        # 查找标签输入区域
        selectors = [
            '[class*="tag"] input',
            'input[placeholder*="标签"]',
            'input[placeholder*="话题"]',
        ]

        for tag in tags[:5]:  # 限制标签数量
            for selector in selectors:
                try:
                    ele = self.page.ele(selector, timeout=1)
                    if ele:
                        # 输入标签
                        tag_text = f"#{tag}" if not tag.startswith('#') else tag
                        ele.input(tag_text)
                        time.sleep(0.5)
                        # 按回车确认
                        ele.input('\n')
                        time.sleep(0.5)
                        break
                except Exception:
                    pass

    def _click_publish(self) -> bool:
        """点击发布按钮"""
        selectors = [
            'button:contains("发布")',
            '[class*="publish"] button',
            'button[class*="submit"]',
            'button[type="submit"]',
        ]

        for selector in selectors:
            try:
                ele = self.page.ele(selector, timeout=2)
                if ele:
                    ele.click()
                    return True
            except Exception:
                pass

        return False

    def _wait_for_publish_complete(self, timeout: int = 60) -> bool:
        """等待发布完成

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否完成
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 检查成功提示
                success_selectors = [
                    ':contains("发布成功")',
                    ':contains("已发布")',
                    '[class*="success"]',
                ]
                for selector in success_selectors:
                    ele = self.page.ele(selector, timeout=1)
                    if ele:
                        return True

                # 检查是否跳转到作品列表
                if 'content/manage' in self.page.url:
                    return True

            except Exception:
                pass

            time.sleep(2)

        return False

    def batch_upload(
        self,
        videos: List[ExportedVideo],
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        delay_between: int = 60
    ) -> List[ExportedVideo]:
        """批量上传视频

        Args:
            videos: 视频列表
            on_log: 日志回调
            on_progress: 进度回调
            delay_between: 每个视频之间的延迟(秒)

        Returns:
            上传成功的视频列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)

        uploaded = []
        total = len(videos)

        for i, video in enumerate(videos):
            log(f"\n[{i+1}/{total}] 上传视频: {video.title or video.video_id}")

            if on_progress:
                on_progress(f"上传 {i+1}/{total}", i+1, total)

            success = self.upload_video(video, on_log)
            if success:
                uploaded.append(video)
                log(f"  成功")
            else:
                log(f"  失败")

            # 延迟，避免频繁操作
            if i < total - 1 and delay_between > 0:
                log(f"等待 {delay_between} 秒...")
                time.sleep(delay_between)

        log(f"\n上传完成: {len(uploaded)}/{total}")
        return uploaded
